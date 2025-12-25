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

#ifndef STST_FIELDMAP_HPP
#define STST_FIELDMAP_HPP

#include "structstore/stst_alloc.hpp"
#include "structstore/stst_field.hpp"
#include "structstore/stst_typing.hpp"
#include "structstore/stst_utils.hpp"

#include <type_traits>

#include <yaml-cpp/yaml.h>

namespace structstore {

class py;

// base class for managed and unmanaged FieldMap.
// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
class FieldMapBase {
protected:
    OffsetPtr<SharedAlloc> sh_alloc;
    shr_unordered_map<shr_string_idx, Field> fields;
    shr_vector<shr_string_idx> slots;

    // constructor, assignment, destructor

    explicit FieldMapBase(SharedAlloc& sh_alloc)
        : sh_alloc(&sh_alloc), fields(0, StlAllocator<>(sh_alloc)),
          slots(StlAllocator<>(sh_alloc)) {
        STST_LOG_DEBUG() << "constructing FieldMap at " << this << " with alloc at " << &sh_alloc
                         << " (static alloc: " << (&sh_alloc == &static_alloc) << ")";
    }

public:
    FieldMapBase(const FieldMapBase& other) = delete;
    FieldMapBase(FieldMapBase&& other) = delete;
    inline FieldMapBase& operator=(const FieldMapBase& other) = delete;
    FieldMapBase& operator=(FieldMapBase&& other) = delete;

    // FieldTypeBase utility functions

    void to_text(std::ostream&) const;

    YAML::Node to_yaml() const;

    void check(const SharedAlloc* sh_alloc, const FieldTypeBase& parent_field) const;

    bool equal_slots(const FieldMapBase& other) const;

    bool operator==(const FieldMapBase& other) const;

    inline bool operator!=(const FieldMapBase& other) const { return !(*this == other); }

    // query operations

    inline bool empty() const { return slots.empty(); }

    inline SharedAlloc& get_alloc() { return *sh_alloc; }

    inline const SharedAlloc& get_alloc() const { return *sh_alloc; }

    inline const shr_vector<shr_string_idx>& get_slots() const { return slots; }

    Field* try_get_field(const std::string& name);

    const Field* try_get_field(const std::string& name) const;

    inline Field& at(const std::string& name) {
        return fields.at(sh_alloc->strings().get_idx(name, *sh_alloc));
    }

    inline const Field& at(const std::string& name) const {
        return fields.at(sh_alloc->strings().get_idx(name, *sh_alloc));
    }

    inline Field& at(shr_string_idx name_idx) { return fields.at(name_idx); }

    inline const Field& at(shr_string_idx name_idx) const { return fields.at(name_idx); }
};

// todo: when returning a FieldAccess, there should be a read lock on the parent FieldMap

// in this managed FieldMap, the contained fields are allocated and constructed.
// instances of this class reside in shared memory, thus no raw pointers
// or references should be used; use structstore::OffsetPtr<T> instead.
class FieldMap : public FieldMapBase, public FieldType<FieldMap> {
    friend class ::structstore::typing;
    friend class ::structstore::SharedAlloc;
    friend class ::structstore::StlAllocator<FieldMap>;
    friend class ::structstore::StructStore;
    friend class ::structstore::py;

public:
    inline static const TypeInfo& type_info = register_type<FieldMap>("structstore::FieldMap");

protected:
    FieldMap(const FieldMap& other) : FieldMap{static_alloc} { *this = other; }

    void copy_from(const FieldMap& other, const FieldTypeBase* parent_field);

public:
    // constructor, assignment, destructor

    explicit FieldMap(SharedAlloc& sh_alloc);

    inline FieldMap& operator=(const FieldMap& other) {
        copy_from(other, this);
        return *this;
    }

    FieldMap(FieldMap&& other) = delete;
    FieldMap& operator=(FieldMap&& other) = delete;

    ~FieldMap() {
        STST_LOG_DEBUG() << "deconstructing FieldMap at " << this;
        clear();
    }

    // FieldTypeBase utility functions

    void check(const SharedAlloc* sh_alloc = nullptr) const;

    // query operations

    FieldAccess at(const std::string& name);

    // insert operations

    FieldAccess operator[](const std::string& name);

    template<typename T>
    T& get(const std::string& name) {
        return (*this)[name];
    }

    FieldMap& substore(const std::string& name) { return get<FieldMap>(name); }

    // remove operations

    void clear();

    void remove(const std::string& name);
};

static_assert(std::is_same_v<unwrap_type_t<FieldRef<FieldMap>>, FieldMap>);
static_assert(std::is_same_v<wrap_type_w<FieldMap>, FieldRef<FieldMap>>);
static_assert(typing::is_field_type<FieldMap>);

} // namespace structstore

#endif
