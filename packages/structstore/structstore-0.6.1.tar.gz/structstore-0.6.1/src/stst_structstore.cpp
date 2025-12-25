// This file is part of the StructStore library.
// Copyright (C) 2022-2025 Max Mertens
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License v3.0
// as published by the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU General Lesser Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

#include "structstore/stst_structstore.hpp"
#include "structstore/stst_alloc.hpp"
#include "structstore/stst_callstack.hpp"
#include "structstore/stst_utils.hpp"
#include <cstdint>
#include <fcntl.h>
#include <memory>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

using namespace structstore;

static std::unordered_map<uint32_t, std::set<MmapHelper*>> alloc_id_map = {};

static StructStore static_store{""};
SharedAlloc& structstore::static_alloc = static_store->get_alloc();

// todo: provide a .to_local() method to get a FieldMap copy using static_alloc

void FD::close() {
    if (fd == -1) { return; }
    ::close(fd);
    fd = -1;
}

StructStore::SharedData::SharedData(size_t size, void* buffer)
    : size{size}, usage_count{1},
      sh_alloc{(uint8_t*) buffer + sizeof(SharedData), size - sizeof(SharedData)},
      invalidated{false} {
    fields = sh_alloc.allocate<FieldMap>();
    new (fields.get()) FieldMap(sh_alloc);
}

void StructStore::register_alloc_id() {
    // store alloc_id to MmapHelper mapping
    const uint32_t alloc_id = sh_data_ptr->sh_alloc.get_id();
    alloc_id_map[alloc_id].insert(mmap_man.get());
}

void StructStore::unregister_alloc_id() {
    // remove alloc_id to MmapHelper mapping
    const uint32_t alloc_id = sh_data_ptr->sh_alloc.get_id();
    alloc_id_map[alloc_id].erase(mmap_man.get());
}

StructStore::StructStore(const std::string& path_, size_t size, bool reinit, bool use_file_,
                         CleanupMode cleanup_)
    : path{path_}, use_file{use_file_}, cleanup{cleanup_} {

    stst_assert(size > sizeof(SharedData));
    if (path.empty()) {
        path = "/dev/shm/structstore_anon_XXXXXX";
        fd = FD(mkstemp(path.data()));
        use_file = true;
        cleanup = IF_LAST;
        stst_assert(fd.get() != -1);
    } else if (use_file) {
        fd = FD(open(path.c_str(), O_EXCL | O_CREAT | O_RDWR, 0600));
    } else {
        fd = FD(shm_open(path.c_str(), O_EXCL | O_CREAT | O_RDWR, 0600));
    }

    bool created = fd.get() != -1;

    if (!created) {
        if (use_file) {
            fd = FD(open(path.c_str(), O_RDWR, 0600));
        } else {
            fd = FD(shm_open(path.c_str(), O_RDWR, 0600));
        }
    }

    if (fd.get() == -1) { throw std::runtime_error("opening shared memory failed"); }

    struct stat fd_state = {};
    fstat(fd.get(), &fd_state);

    if (reinit && fd_state.st_size != 0) {
        // we found an opened memory segment with a non-zero size,
        // it's likely an old segment thus ...

        // ... we open it and mark it as closed ...
        mmap_man = MmapHelper::mmap_existing_fd(fd.get());
        sh_data_ptr = (SharedData*) mmap_man->get_data();
        sh_data_ptr->invalidated.store(true);
        sh_data_ptr->usage_count -= 1;

        // ... then unmap it, ...
        mmap_man.reset();
        sh_data_ptr = nullptr;

        // ... then unlink it, ...
        if (use_file) {
            unlink(path.c_str());
        } else {
            shm_unlink(path.c_str());
        }

        // ... and finally recreate it
        if (use_file) {
            fd = FD(open(path.c_str(), O_EXCL | O_CREAT | O_RDWR, 0600));
        } else {
            fd = FD(shm_open(path.c_str(), O_EXCL | O_CREAT | O_RDWR, 0600));
        }

        if (fd.get() == -1) { throw std::runtime_error("opening shared memory failed"); }
    } else if (!created && fd_state.st_mode == 0100600) {
        // shared memory is not ready for opening yet
        throw std::runtime_error("shared memory not initialized yet");
    }

    if (created || reinit) {
        mmap_man = MmapHelper::mmap_new_fd(fd.get(), size);
        sh_data_ptr = (SharedData*) mmap_man->get_data();

        // initialize data
        static_assert((sizeof(SharedData) % 8) == 0);
        new (sh_data_ptr) SharedData(size, sh_data_ptr);
        STST_LOG_DEBUG() << "created shared FieldMap at " << sh_data_ptr;

        // marks the fields as ready to be used
        fchmod(fd.get(), 0660);
    } else {
        mmap_man = MmapHelper::mmap_existing_fd(fd.get());
        sh_data_ptr = (SharedData*) mmap_man->get_data();
        STST_LOG_DEBUG() << "opened shared FieldMap at " << sh_data_ptr;
        ++sh_data_ptr->usage_count;
    }
    register_alloc_id();
}

bool StructStore::valid() const {
    return sh_data_ptr != nullptr && !sh_data_ptr->invalidated.load();
}

void StructStore::assert_valid() const {
    if (sh_data_ptr == nullptr) { throw std::runtime_error("StructStore instance is invalid"); }
}

bool StructStore::revalidate(bool block) {

    if (valid()) { return true; }

    // need to revalidate the shared memory segment

    FD new_fd;

    do {
        if (new_fd.get() == -1) {
            if (use_file) {
                new_fd = FD(open(path.c_str(), O_RDWR, 0600));
            } else {
                new_fd = FD(shm_open(path.c_str(), O_RDWR, 0600));
            }
            if (new_fd.get() == -1) { continue; }
        }

        struct stat fd_stat = {};
        fstat(new_fd.get(), &fd_stat);

        // check if segment is ready
        if (fd_stat.st_mode == 0100660) {
            unregister_alloc_id();
            // map new segment
            fd = std::move(new_fd);
            mmap_man = MmapHelper::mmap_existing_fd(fd.get());
            sh_data_ptr = (SharedData*) mmap_man->get_data();
            register_alloc_id();
            return true;
        }

        // backoff time, while doing busy waiting
        if (block) { usleep(1000); }

    } while (block);

    return false;
}


void StructStore::close() {
    if (sh_data_ptr == nullptr) { return; }

    if (((--sh_data_ptr->usage_count == 0 && cleanup == IF_LAST) || cleanup == ALWAYS)) {
        bool expected = false;
        // if cleanup == ALWAYS this ensure that unlink is done exactly once
        if (sh_data_ptr->invalidated.compare_exchange_strong(expected, true,
                                                             std::memory_order_acquire)) {
            STST_LOG_DEBUG() << "deconstr shared Store";
            sh_data_ptr->fields->~FieldMap();
            STST_LOG_DEBUG() << "dealloc shared Store";
            sh_data_ptr->sh_alloc.deallocate(sh_data_ptr->fields.get());
            STST_LOG_DEBUG() << "dealloc shared alloc";
            sh_data_ptr->sh_alloc.~SharedAlloc();
            STST_LOG_DEBUG() << "unlink";
            if (use_file) {
                unlink(path.c_str());
            } else {
                shm_unlink(path.c_str());
            }
        }
    }

    unregister_alloc_id();
    mmap_man.reset();
    sh_data_ptr = nullptr;
}

void StructStore::to_buffer(void* buffer, size_t bufsize) const {
    assert_valid();
    if (bufsize < sh_data_ptr->size) { throw std::runtime_error("target buffer too small"); }
    std::memcpy((void*) buffer, sh_data_ptr, sh_data_ptr->size);
}

void StructStore::from_buffer(void* buffer, size_t bufsize) {
    assert_valid();
    if (bufsize < ((SharedData*) buffer)->size) {
        throw std::runtime_error("source buffer too small");
    }
    std::memcpy((void*) sh_data_ptr, buffer, ((SharedData*) buffer)->size);
}

bool StructStore::operator==(const StructStore& other) const {
    assert_valid();
    other.assert_valid();
    return *sh_data_ptr->fields == *other.sh_data_ptr->fields;
}

void StructStore::check() const {
    CallstackEntry entry{"structstore::StructStore::check()"};
    sh_data_ptr->fields->check(&sh_data_ptr->sh_alloc);
}

bool structstore::mmap_helper_change_size(uint64_t alloc_id, int64_t sizediff) {
    auto it = alloc_id_map.find(alloc_id);
    if (it == alloc_id_map.end()) { return false; }
    // get any MmapHelper
    MmapHelper* mmap_helper = *it->second.begin();
    mmap_helper->change_size(sizediff);
    return true;
}
