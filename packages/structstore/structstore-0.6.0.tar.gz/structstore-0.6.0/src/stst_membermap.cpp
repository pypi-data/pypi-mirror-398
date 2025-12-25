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

#include "structstore/stst_membermap.hpp"
#include "structstore/stst_alloc.hpp"
#include "structstore/stst_callstack.hpp"
#include "structstore/stst_field.hpp"
#include "structstore/stst_offsetptr.hpp"
#include "structstore/stst_struct.hpp"
#include "structstore/stst_utils.hpp"
#include <cstddef>

using namespace structstore;

const void* MemberInfo::get_ptr(const StructBase& self) const {
    auto ptr = (const void*) ((ptrdiff_t) &self + offset);
    STST_LOG_DEBUG() << "member " << name << " at " << ptr;
    return ptr;
}

void* MemberInfo::get_ptr(StructBase& self) const {
    auto ptr = (void*) ((ptrdiff_t) &self + offset);
    STST_LOG_DEBUG() << "member " << name << " at " << ptr;
    return ptr;
}

FieldViewConst MemberInfo::get_view(const StructBase& self) const {
    return FieldViewConst{(void*) get_ptr(self), type_hash};
}

FieldView MemberInfo::get_view(StructBase& self) const {
    return FieldView{get_ptr(self), type_hash};
}

void MemberMap::store_ref(const std::string& name, ptrdiff_t member_offs, type_hash_t type_hash) {
    STST_LOG_DEBUG() << "registering unmanaged data in MemberMap at " << this << " with alloc at "
                     << sh_alloc.get() << " (static alloc: " << (sh_alloc.get() == &static_alloc)
                     << ")";
    shr_string name_{name, StlAllocator{*sh_alloc}};
    stst_assert(member_offs >= 0);
    stst_assert(member_offs < (1l << 31));
    const MemberInfo member_info = {(int32_t) member_offs, type_hash, name_};
    auto [it, inserted] = member_idx.emplace(name_, members.size());
    if (!inserted) { throw std::runtime_error("field name already exists"); }
    members.emplace_back(member_info);
}

MemberMap::MemberMap(SharedAlloc& sh_alloc)
    : sh_alloc{&sh_alloc}, members{StlAllocator<int>{sh_alloc}},
      member_idx{StlAllocator<int>{sh_alloc}}, init_done{false} {}

void MemberMap::copy_from(StructBase& self, const StructBase& other) const {
    // unmanaged copy: slots have to be the same
    STST_LOG_DEBUG() << "copying unmanaged MemberMap from " << &other << " into " << &self;
    for (const MemberInfo& member_info: members) {
        void* member_self = member_info.get_ptr(self);
        const void* member_other = member_info.get_ptr(other);
        const auto& type_info = typing::get_type(member_info.type_hash);
        type_info.copy_fn(*sh_alloc, member_self, member_other);
    }
    STST_LOG_DEBUG() << "copy done";
}

void MemberMap::to_text(const StructBase& self, std::ostream& os) const {
    STST_LOG_DEBUG() << "serializing MemberMap at " << &self;
    os << "{";
    for (const MemberInfo& member_info: members) {
        const void* member_self = member_info.get_ptr(self);
        os << '"' << member_info.name << "\":";
        const auto& type_info = typing::get_type(member_info.type_hash);
        type_info.serialize_text_fn(os, member_self);
        os << ",";
    }
    os << "}";
}

YAML::Node MemberMap::to_yaml(const StructBase& self) const {
    YAML::Node root(YAML::NodeType::Map);
    for (const MemberInfo& member_info: members) {
        const void* member_self = member_info.get_ptr(self);
        const auto& type_info = typing::get_type(member_info.type_hash);
        root[member_info.name.c_str()] = type_info.serialize_yaml_fn(member_self);
    }
    return root;
}

void MemberMap::check(const StructBase& self, const SharedAlloc* sh_alloc,
                      const FieldTypeBase& parent_field) const {
    CallstackEntry entry{"structstore::MemberMap::check()"};
    if (sh_alloc) {
        stst_assert(this->sh_alloc.get() == sh_alloc);
    } else {
        // use our own reference instead
        sh_alloc = this->sh_alloc.get();
    }
    // this could be allocated on regular stack/heap if the owning FieldMap is not in shared mem
    stst_assert(sh_alloc == &static_alloc || sh_alloc->is_owned(&self));
    for (const MemberInfo& member_info: members) {
        STST_LOG_DEBUG() << "checking " << member_info.name << " at " << member_info.get_ptr(self);
        member_info.get_view(self).check(*sh_alloc, parent_field);
    }
}

bool MemberMap::equals(const StructBase& self, const StructBase& other) const {
    for (const MemberInfo& member_info: members) {
        const void* member_self = member_info.get_ptr(self);
        const void* member_other = member_info.get_ptr(other);
        const auto& type_info = typing::get_type(member_info.type_hash);
        if (!type_info.cmp_equal_fn(member_self, member_other)) { return false; }
    }
    return true;
}

FieldViewConst MemberMap::get_member(const std::string& name, const StructBase& stru) const {
    shr_string name_{name, StlAllocator{*sh_alloc}};
    auto it = member_idx.find(name_);
    if (it == member_idx.end()) { return FieldViewConst{nullptr, 0}; }
    const MemberInfo& member_info = members.at(it->second);
    return member_info.get_view(stru);
}

FieldView MemberMap::get_member(const std::string& name, StructBase& stru) const {
    shr_string name_{name, StlAllocator{*sh_alloc}};
    auto it = member_idx.find(name_);
    if (it == member_idx.end()) { return FieldView{nullptr, 0}; }
    const MemberInfo& member_info = members.at(it->second);
    return member_info.get_view(stru);
}

MemberMapStorage::MemberMapStorage(SharedAlloc& sh_alloc)
    : member_maps{StlAllocator<int>(sh_alloc)} {
    STST_LOG_DEBUG() << "constructing MemberMapStorage at " << this;
}

MemberMapStorage::~MemberMapStorage() { stst_assert(member_maps.empty()); }

MemberMap* MemberMapStorage::get(const type_hash_t type_hash) {
    stst_assert(type_hash != 0);
    ScopedLock<false> lock{mutex};
    auto it = member_maps.find(type_hash);
    if (it == member_maps.end()) { return nullptr; }
    return it->second.get();
}

MemberMap& MemberMapStorage::create(const type_hash_t type_hash, SharedAlloc& sh_alloc) {
    stst_assert(type_hash != 0);
    MemberMap* member_map = sh_alloc.allocate<MemberMap>();
    new (member_map) MemberMap(sh_alloc);
    ScopedLock<true> lock{mutex};
    auto [it, inserted] = member_maps.emplace(type_hash, nullptr);
    stst_assert(inserted);
    it->second = member_map;
    return *it->second;
}

void MemberMapStorage::clear(SharedAlloc& sh_alloc) {
    for (auto it = member_maps.begin(); it != member_maps.end(); ++it) {
        it->second->~MemberMap();
        sh_alloc.deallocate(it->second.get());
    }
    member_maps.clear();
}
