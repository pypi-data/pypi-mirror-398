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

#include "structstore/stst_alloc.hpp"
#include "structstore/stst_utils.hpp"
#include "structstore/stst_membermap.hpp"
#include <random>

using namespace structstore;

static std::mt19937_64 alloc_id_rnd{generate_rnd_seed()};

SharedAlloc::SharedAlloc(void* buffer, size_t size)
    : blocksize{size}, mm{(mini_malloc*) buffer}, string_storage{nullptr} {
    if (buffer == nullptr) { return; }
    stst_assert(size < (1ull << 31));
    init_mini_malloc(mm.get(), size);
    string_storage = allocate<StringStorage>();
    new (string_storage.get()) StringStorage(*this);
    member_map_storage = allocate<MemberMapStorage>();
    new (member_map_storage.get()) MemberMapStorage(*this);
    alloc_id = alloc_id_rnd();
}

SharedAlloc::~SharedAlloc() noexcept(false) {
    STST_LOG_DEBUG() << "SharedAlloc: deconstruct StringStorage at " << string_storage.get();
    string_storage->~StringStorage();
    STST_LOG_DEBUG() << "SharedAlloc: dealloc StringStorage";
    deallocate(string_storage.get());
    STST_LOG_DEBUG() << "SharedAlloc: deconstruct MemberMapStorage at " << member_map_storage.get();
    member_map_storage->clear(*this);
    member_map_storage->~MemberMapStorage();
    STST_LOG_DEBUG() << "SharedAlloc: dealloc MemberMapStorage";
    deallocate(member_map_storage.get());
    STST_LOG_DEBUG() << "SharedAlloc: check for leaks";
    mm_assert_all_freed(mm.get());
}

void* SharedAlloc::allocate_(size_t field_size) {
    if (field_size == 0) { field_size = ALIGN; }
    ScopedLock<true> lock{mutex};
    void* ptr = mm_allocate(mm.get(), field_size);
    if (ptr == nullptr) {
        // enlarge memory block by at least 25%
        size_t sizediff = field_size + 8; // add ALLOC_NODE_SIZE
        size_t min_sizediff = std::min<size_t>(blocksize / 4, 1ll << 30);
        sizediff = min_sizediff > sizediff ? min_sizediff : sizediff;
        if (sizediff % PAGESIZE) {
            sizediff += PAGESIZE - sizediff % PAGESIZE;
        }
        if (mmap_helper_change_size(alloc_id, sizediff)) {
            mm_enlarge(mm.get(), sizediff);
            blocksize += sizediff;
            // retry allocation
            ptr = mm_allocate(mm.get(), field_size);
        }
    }
    if (ptr == nullptr) {
        std::ostringstream str;
        str << "insufficient space in sh_alloc region, requested: " << field_size;
        Callstack::warn_with_trace(str.str());
        throw std::bad_alloc();
    }
    assert((size_t) ptr % ALIGN == 0);
    return ptr;
}

void SharedAlloc::deallocate(const void* ptr) {
    STST_LOG_DEBUG() << "deallocating at " << ptr;
    ScopedLock<true> lock{mutex};
    mm_free(mm.get(), ptr);
}

bool SharedAlloc::is_owned(const void* ptr) const {
    if (ptr == nullptr) {
#ifndef NDEBUG
        Callstack::warn_with_trace("checked pointer is null");
#endif
        return false;
    }
    if (ptr < (byte*) mm.get() || ptr >= (byte*) mm.get() + blocksize) {
#ifndef NDEBUG
        Callstack::warn_with_trace("checked pointer is outside arena");
#endif
        return false;
    }
    return true;
}

StringStorage::StringStorage(SharedAlloc& sh_alloc)
    : map{StlAllocator<int>(sh_alloc)}, data{StlAllocator<int>(sh_alloc)} {
    STST_LOG_DEBUG() << "constructing StringStorage at " << this;
    // element 0 is none
    data.emplace_back();
}

shr_string_idx StringStorage::internalize(const std::string& str, SharedAlloc& sh_alloc) {
    stst_assert(str != "");
    if (shr_string_idx found_idx = get_idx(str, sh_alloc)) { return found_idx; }
    shr_string str_{str, StlAllocator{sh_alloc}};
    ScopedLock<true> lock{mutex};
    auto [it, inserted] = map.emplace(str_, 0);
    if (inserted) {
        it->second = data.size();
        stst_assert(data.size() < 8191);
        data.emplace_back(str_);
    } else {
        stst_assert(it->second > 0);
    }
    return it->second;
}

shr_string_idx StringStorage::get_idx(const std::string& str, SharedAlloc& sh_alloc) const {
    stst_assert(str != "");
    shr_string str_{str, StlAllocator{sh_alloc}};
    ScopedLock<false> lock{mutex};
    auto it = map.find(str_);
    if (it != map.end()) { return it->second; }
    return 0;
}

const shr_string* StringStorage::get(shr_string_idx idx) const { return &data[idx]; }
