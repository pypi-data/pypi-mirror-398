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

#ifndef STST_STRUCTSTORE_HPP
#define STST_STRUCTSTORE_HPP

#include "structstore/stst_alloc.hpp"
#include "structstore/stst_field.hpp"
#include "structstore/stst_fieldmap.hpp"
#include "structstore/stst_mmap.hpp"
#include "structstore/stst_utils.hpp"

namespace structstore {

enum CleanupMode { NEVER, IF_LAST, ALWAYS };

class FD {
    FD(const FD&) = delete;

    FD& operator=(const FD&) = delete;

    int fd;

public:
    FD() : fd(-1) {}

    explicit FD(int fd) : fd(fd) {}

    FD(FD&& other) noexcept : FD() { *this = std::move(other); }

    FD& operator=(FD&& other) noexcept {
        std::swap(fd, other.fd);
        return *this;
    }

    ~FD() { close(); }

    [[nodiscard]] int get() const { return fd; }

    void close();

    void release() { fd = -1; }
};

class StructStore {
protected:
    // instances of this class reside in shared memory, thus no raw pointers
    // or references should be used; use structstore::OffsetPtr<T> instead.
    struct SharedData {
        size_t size;
        std::atomic_int32_t usage_count;
        SharedAlloc sh_alloc;
        OffsetPtr<FieldMap> fields;
        std::atomic_bool invalidated;

        SharedData(size_t size, void* buffer);

        SharedData() = delete;

        SharedData(SharedData&&) = delete;

        SharedData(const SharedData&) = delete;

        SharedData& operator=(SharedData&&) = delete;

        SharedData& operator=(const SharedData&) = delete;

        ~SharedData() = delete;
    };

    // init data
    std::string path{};
    bool use_file = false;
    CleanupMode cleanup = NEVER;

    // generated data
    FD fd = {};
    std::unique_ptr<MmapHelper> mmap_man = {};
    SharedData* sh_data_ptr = nullptr;

    StructStore(const StructStore&) = delete;

    StructStore& operator=(const StructStore&) = delete;

    void register_alloc_id();

    void unregister_alloc_id();

public:
    explicit StructStore(const std::string& path, size_t size = 4096, bool reinit = false,
                         bool use_file = false, CleanupMode cleanup = IF_LAST);

    StructStore(StructStore&& other) noexcept { *this = std::move(other); }

    StructStore& operator=(StructStore&& other) noexcept {
        std::swap(path, other.path);
        std::swap(use_file, other.use_file);
        std::swap(cleanup, other.cleanup);

        std::swap(fd, other.fd);
        std::swap(mmap_man, other.mmap_man);
        std::swap(sh_data_ptr, other.sh_data_ptr);
        return *this;
    }

    bool valid() const;

    void assert_valid() const;

    bool revalidate(bool block = true);

    FieldMap* operator->() {
        assert_valid();
        return sh_data_ptr->fields.get();
    }

    FieldMap& operator*() {
        assert_valid();
        return *sh_data_ptr->fields.get();
    }

    FieldAccess operator[](const std::string& name) {
        assert_valid();
        return (*sh_data_ptr->fields)[name];
    }

    ~StructStore() {
        STST_LOG_DEBUG() << "deconstructing shared FieldMap at " << sh_data_ptr;
        close();
    }

    void close();

    const void* addr() const {
        assert_valid();
        return sh_data_ptr;
    }

    size_t size() const {
        assert_valid();
        return sh_data_ptr->size;
    }

    void to_buffer(void* buffer, size_t bufsize) const;

    void from_buffer(void* buffer, size_t bufsize);

    bool operator==(const StructStore& other) const;

    inline bool operator!=(const StructStore& other) const { return !(*this == other); }

    void check() const;
};

template<>
struct Unwrapper<StructStore> {
    using T = FieldMap;
    FieldMap& t;
    Unwrapper(StructStore& w) : t{*w} {}
};
static_assert(std::is_same_v<unwrap_type_t<StructStore>, FieldMap>);
static_assert(std::is_same_v<wrap_type_w<StructStore>, StructStore&>);

} // namespace structstore

#endif
