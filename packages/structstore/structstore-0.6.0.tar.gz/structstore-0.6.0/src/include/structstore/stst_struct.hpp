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

#ifndef STST_STRUCT_HPP
#define STST_STRUCT_HPP

#include "structstore/stst_alloc.hpp"
#include "structstore/stst_callstack.hpp"
#include "structstore/stst_membermap.hpp"
#include "structstore/stst_typing.hpp"

namespace structstore {

class py;

// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
class StructBase {
    template<typename T>
    friend class Struct;
    friend class structstore::py;

private:
    // only to be accessed by Struct<T>, not by subclasses thereof
    OffsetPtr<MemberMap> member_map;

    inline void copy_from(const StructBase& other) { member_map->copy_from(*this, other); }

    inline FieldViewConst get_member(const std::string& name) const {
        return member_map->get_member(name, *this);
    }

    inline FieldView get_member(const std::string& name) {
        return member_map->get_member(name, *this);
    }

    inline const MemberMap& get_member_map() const { return *member_map; }

    inline SharedAlloc& get_alloc() { return member_map->get_alloc(); }

protected:
    explicit StructBase(SharedAlloc& sh_alloc, type_hash_t type_hash);

public:
    // FieldTypeBase utility functions

    inline void to_text(std::ostream& os) const { member_map->to_text(*this, os); }

    inline YAML::Node to_yaml() const { return member_map->to_yaml(*this); }
};

// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
template<typename T>
class Struct : public FieldType<T>, public StructBase {
protected:
    // constructor, assignment, destructor

    Struct() : Struct(static_alloc) {}

    explicit Struct(SharedAlloc& sh_alloc) : StructBase{sh_alloc, typing::get_type_hash<T>()} {}

    Struct(const Struct&) = delete;
    Struct(Struct&&) = delete;
    Struct& operator=(const Struct&) = delete;
    Struct& operator=(Struct&&) = delete;

    template<typename U>
    void store_ref(const std::string& name, U& u) {
        if constexpr (std::is_base_of_v<FieldTypeBase, U>) {
            const FieldTypeBase& this_base = *this;
            u.parent_field = &this_base;
        }
        if (!member_map->is_init_done()) { member_map->store_ref<U>(name, *this, u); }
    }

    inline void copy_from(const T& other) {
        StructBase::copy_from(other);
    }

public:
    // FieldTypeBase utility functions

    void check(const SharedAlloc* sh_alloc = nullptr) const {
        CallstackEntry entry{"structstore::Struct::check()"};
        const FieldTypeBase& this_base = *this;
        member_map->check(*this, sh_alloc, this_base);
    }

    inline bool operator==(const T& other) const { return member_map->equals(*this, other); }

    inline bool operator!=(const T& other) const { return !(*this == other); }
};

} // namespace structstore

#endif
