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

#ifndef STST_ALLOC_HPP
#define STST_ALLOC_HPP

#include "ankerl/unordered_dense.h"
#include "structstore/mini_malloc.hpp"
#include "structstore/stst_lock.hpp"
#include "structstore/stst_offsetptr.hpp"
#include "structstore/stst_utils.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <functional>
#include <type_traits>

namespace structstore {

class StringStorage;

bool mmap_helper_change_size(uint64_t alloc_id, int64_t sizediff);

// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
class SharedAlloc {
    using byte = uint8_t;
    static constexpr size_t ALIGN = 8;
    static constexpr size_t PAGESIZE = 4096;

    // member variables
    size_t blocksize;
    OffsetPtr<mini_malloc> mm;
    SpinMutex mutex;
    OffsetPtr<StringStorage> string_storage;

    // unique random ID for the mapping of a SharedAlloc instance
    // (in shared mem) to a process-local MmapHelper instance
    uint32_t alloc_id;

    void* allocate_(size_t field_size);

public:
    SharedAlloc(void* buffer, size_t size);

    ~SharedAlloc() noexcept(false);

    SharedAlloc() = delete;
    SharedAlloc(SharedAlloc&&) = delete;
    SharedAlloc(const SharedAlloc&) = delete;
    SharedAlloc& operator=(SharedAlloc&&) = delete;
    SharedAlloc& operator=(const SharedAlloc&) = delete;

    template<typename T = void>
    T* allocate(size_t field_size = sizeof(T)) {
        void* ptr = allocate_(field_size);
        STST_LOG_DEBUG() << "allocating " << typeid(T).name() << " at " << ptr;
        return (T*) ptr;
    }

    void deallocate(const void* ptr);

    bool is_owned(const void* ptr) const;

    inline StringStorage& strings() { return *string_storage.get(); }

    inline const StringStorage& strings() const { return *string_storage.get(); }

    inline uint32_t get_id() const { return alloc_id; }

    inline size_t get_allocated_size() const { return mm_get_allocated_size(mm.get()); }
};

// this is a dummy reference pointing to nullptr
extern SharedAlloc& nullptr_alloc;

// the instance is defined in stst_structstore.cpp,
// as it uses a full anonymous StructStore instance
// for the dynamic memory resizing feature
extern SharedAlloc& static_alloc;

class FieldMap;

// instances of this class can reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
template<typename T = char>
class StlAllocator {
    template<typename U>
    friend class StlAllocator;

    OffsetPtr<SharedAlloc, int64_t> sh_alloc;

public:
    using value_type = T;
    using pointer = OffsetPtr<T, int64_t>;

    explicit StlAllocator(SharedAlloc& a) : sh_alloc(&a) {}

    template<typename U>
    StlAllocator(const StlAllocator<U>& other) : sh_alloc(other.sh_alloc.get()) {}

    T* allocate(std::size_t n) { return static_cast<T*>(sh_alloc->allocate(n * sizeof(T))); }

    void deallocate(T* p, std::size_t) { sh_alloc->deallocate(p); }
    void deallocate(const OffsetPtr<T, int32_t>& p, std::size_t) { sh_alloc->deallocate(p.get()); }
    void deallocate(const OffsetPtr<T, int64_t>& p, std::size_t) { sh_alloc->deallocate(p.get()); }

    void construct(T* p) {
        if constexpr (std::is_constructible_v<T, SharedAlloc&> || std::is_same_v<T, FieldMap>) {
            new (p) T(*sh_alloc);
        } else if constexpr (std::is_constructible_v<T, const StlAllocator<T>&>) {
            new (p) T(StlAllocator<T>{*sh_alloc});
        } else {
            new (p) T();
        }
    }

    void construct(T* p, T&& other) { new (p) T(std::move(other)); }

    void construct(T* p, const T& other) { new (p) T(other); }

    template<typename U>
    bool operator==(StlAllocator<U> const& rhs) const {
        return sh_alloc.get() == rhs.sh_alloc.get();
    }

    template<typename U>
    bool operator!=(StlAllocator<U> const& rhs) const {
        return sh_alloc.get() != rhs.sh_alloc.get();
    }

    SharedAlloc& get_alloc() { return *sh_alloc; }
};

using shr_string = std::basic_string<char, std::char_traits<char>, StlAllocator<char>>;

using shr_string_idx = uint16_t;

template<class T>
using shr_vector = std::vector<T, StlAllocator<T>>;

// todo: use 32bit hashes
template<class K, class T, class H = ankerl::unordered_dense::hash<K>>
using shr_unordered_map = ankerl::unordered_dense::map<K, T, H, std::equal_to<K>,
                                                       StlAllocator<std::pair<const K, T>>>;

// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
class StringStorage {
    shr_unordered_map<shr_string, shr_string_idx> map;
    shr_vector<shr_string> data;
    mutable SpinMutex mutex;

public:
    StringStorage(SharedAlloc& sh_alloc);

    shr_string_idx internalize(const std::string& str, SharedAlloc& sh_alloc);

    shr_string_idx get_idx(const std::string& str, SharedAlloc& sh_alloc) const;

    const shr_string* get(shr_string_idx idx) const;
};

} // namespace structstore

#endif
