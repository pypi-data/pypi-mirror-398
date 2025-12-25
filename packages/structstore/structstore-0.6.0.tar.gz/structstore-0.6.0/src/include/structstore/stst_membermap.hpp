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

#ifndef STST_MEMBERMAP_HPP
#define STST_MEMBERMAP_HPP

#include "structstore/stst_alloc.hpp"
#include "structstore/stst_field.hpp"
#include "structstore/stst_typing.hpp"
#include "structstore/stst_utils.hpp"

#include <cstddef>
#include <stdexcept>
#include <type_traits>

#include <yaml-cpp/yaml.h>

namespace structstore {

class py;

class StructBase;

// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
struct MemberInfo {
    const int32_t offset;
    const type_hash_t type_hash;
    const shr_string name;

    const void* get_ptr(const StructBase& self) const;
    void* get_ptr(StructBase& self) const;

    FieldViewConst get_view(const StructBase& self) const;
    FieldView get_view(StructBase& self) const;
};

// this class stores pointer offsets to struct members.
// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
class MemberMap {
    friend class StructBase;

protected:
    OffsetPtr<SharedAlloc> sh_alloc;
    shr_vector<MemberInfo> members;
    shr_unordered_map<shr_string, uint16_t> member_idx;
    bool init_done;

    void store_ref(const std::string& name, ptrdiff_t member_offs, type_hash_t type_hash);

    inline SharedAlloc& get_alloc() { return *sh_alloc; }

public:
    // constructor, assignment, destructor

    explicit MemberMap(SharedAlloc& sh_alloc);

    MemberMap(MemberMap&&) = delete;
    MemberMap(const MemberMap& other) = delete;
    MemberMap& operator=(MemberMap&& other) = delete;
    MemberMap& operator=(const MemberMap& other) = delete;

    // insert operations

    template<typename T>
    void store_ref(const std::string& name, StructBase& stru, T& t) {
        const ptrdiff_t member_offs = (ptrdiff_t) &t - (ptrdiff_t) &stru;
        store_ref(name, member_offs, typing::get_type_hash<T>());
        STST_LOG_DEBUG() << "field " << name << " at " << &t;
    }

    inline void finish_init() { init_done = true; }

    inline bool is_init_done() const { return init_done; }

    // utility functions for StructBase and Struct<T>

    void copy_from(StructBase& self, const StructBase& other) const;
    void to_text(const StructBase& self, std::ostream& os) const;
    YAML::Node to_yaml(const StructBase& self) const;
    void check(const StructBase& self, const SharedAlloc* sh_alloc,
               const FieldTypeBase& parent_field) const;
    bool equals(const StructBase& self, const StructBase& other) const;

    // other access functions

    const shr_vector<MemberInfo> get_members() const { return members; }

    FieldViewConst get_member(const std::string& name, const StructBase& stru) const;
    FieldView get_member(const std::string& name, StructBase& stru) const;
};

// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
class MemberMapStorage {
    shr_unordered_map<type_hash_t, OffsetPtr<MemberMap>> member_maps;
    mutable SpinMutex mutex;

public:
    MemberMapStorage(SharedAlloc& sh_alloc);
    ~MemberMapStorage();

    MemberMap* get(const type_hash_t type_hash);

    MemberMap& create(const type_hash_t type_hash, SharedAlloc& sh_alloc);

    void clear(SharedAlloc& sh_alloc);
};

} // namespace structstore

#endif
