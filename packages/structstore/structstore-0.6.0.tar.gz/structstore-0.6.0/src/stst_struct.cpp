// This file is part of the MmapHelper library.
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

#include "structstore/stst_struct.hpp"

using namespace structstore;

StructBase::StructBase(SharedAlloc& sh_alloc, type_hash_t type_hash) {
    if (MemberMap* member_map = sh_alloc.member_maps().get(type_hash)) {
        this->member_map = member_map;
        // the previous init should be finished by now; there probably is no better place to call this
        member_map->finish_init();
    } else {
        this->member_map = &sh_alloc.member_maps().create(type_hash, sh_alloc);
    }
}