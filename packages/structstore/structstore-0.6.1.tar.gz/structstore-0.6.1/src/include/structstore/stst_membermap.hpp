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

#include <gtest/gtest.h>
#include <yaml-cpp/yaml.h>

namespace structstore {

class py;

class StructBase;

struct MemberInfo {
    const int32_t offset;
    const type_hash_t type_hash;
    const std::string name;

    const void* get_ptr(const StructBase& self) const;
    void* get_ptr(StructBase& self) const;

    FieldViewConst get_view(const StructBase& self, SharedAlloc& sh_alloc) const;
    FieldView get_view(StructBase& self, SharedAlloc& sh_alloc) const;
};

// this class stores pointer offsets to struct members.
class MemberMap {
    friend class StructBase;

protected:
    std::vector<MemberInfo> members;
    std::unordered_map<std::string, uint16_t> member_idx;
    bool init_done = false;

    void store_ref(const std::string& name, ptrdiff_t member_offs, type_hash_t type_hash);

public:
    // constructor, assignment, destructor

    MemberMap() = default;
    MemberMap(MemberMap&&) = delete;
    MemberMap(const MemberMap& other) = delete;
    MemberMap& operator=(MemberMap&& other) = default;
    MemberMap& operator=(const MemberMap& other) = delete;

    // insert operations

    template<typename T>
    void store_ref(const std::string& name, StructBase& stru, T& t) {
        stst_assert(!init_done);
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

    bool empty() const { return members.empty(); }

    const std::vector<MemberInfo> get_members() const { return members; }

    FieldViewConst get_member(const std::string& name, const StructBase& stru,
                              SharedAlloc& sh_alloc) const;
    FieldView get_member(const std::string& name, StructBase& stru, SharedAlloc& sh_alloc) const;
};

} // namespace structstore

#endif
