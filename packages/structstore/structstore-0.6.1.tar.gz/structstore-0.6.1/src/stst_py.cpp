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

#include "structstore/stst_py.hpp"
#include "structstore/stst_alloc.hpp"
#include "structstore/stst_field.hpp"
#include "structstore/stst_membermap.hpp"
#include "structstore/stst_struct.hpp"
#include "structstore/stst_typing.hpp"
#include "structstore/stst_utils.hpp"

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/make_iterator.h>
#include <nanobind/stl/string.h>

using namespace structstore;

namespace nb = nanobind;

nb::object py::SimpleNamespace;

std::unordered_map<type_hash_t, const py::PyType>& py::get_py_types() {
    static auto* py_types = new std::unordered_map<type_hash_t, const py::PyType>();
    return *py_types;
}

std::unordered_map<std::string, type_hash_t>& py::get_typemap() {
    static auto* typemap = new std::unordered_map<std::string, type_hash_t>();
    return *typemap;
}

const py::PyType& py::get_py_type(type_hash_t type_hash) {
    try {
        return py::get_py_types().at(type_hash);
    } catch (const std::out_of_range&) {
        std::ostringstream str;
        str << "could not find Python type information for type '" << typing::get_type(type_hash).name << "'";
        throw Callstack::exc_with_trace(str.str());
    }
}

type_hash_t py::get_stst_type(const nb::handle& value) {
    // try direct conversion
    std::string type_name = nb::repr(value.type()).c_str();
    const auto& typemap = py::get_typemap();
    auto it = typemap.find(type_name);
    if (it != typemap.end()) { return it->second; }
    // check if casting to dict and representing as FieldMap is possible
    if (nb::hasattr(value, "__dict__") || nb::isinstance<nb::dict>(value) ||
        nb::hasattr(value, "__slots__")) {
        return typemap.at("<class 'dict'>");
    }
    // all attempts failed
    std::ostringstream str;
    str << "could not find corresponding StructStore type for type '" << type_name << "'";
    throw nb::type_error(str.str().c_str());
}

__attribute__((__visibility__("default"))) nb::object
py::member_map_to_python(const MemberMap& member_map, StructBase& stru, SharedAlloc& sh_alloc,
                         py::ToPythonMode mode) {
    CallstackEntry entry{"member_map_to_python()"};
    auto obj = SimpleNamespace();
    for (const MemberInfo& member_info: member_map.get_members()) {
        auto key = nb::str(member_info.name.c_str());
        if (mode == py::ToPythonMode::RECURSIVE) {
            nb::setattr(obj, key,
                        py::to_python(member_info.get_view(stru, sh_alloc),
                                      py::ToPythonMode::RECURSIVE));
        } else { // non-recursive convert
            nb::setattr(obj, key, py::to_python_cast(member_info.get_view(stru, sh_alloc)));
        }
    }
    return obj;
}

__attribute__((__visibility__("default"))) void
py::member_map_from_python(const MemberMap& member_map, StructBase& stru, SharedAlloc& sh_alloc,
                           const nb::handle& value) {
    // todo: strict check if this is one of dict, SimpleNamespace, FieldMap
    if (!nb::isinstance<nb::dict>(value)) { py::throw_convert_error<StructBase>(value); }
    nb::dict dict = nb::cast<nb::dict>(value);
    STST_LOG_DEBUG() << "copying __dict__ to " << &stru;
    if (member_map.get_members().size() != dict.size()) {
        Callstack::throw_with_trace("cannot copy dict with wrong fields into struct");
    }
    for (const MemberInfo& member_info: member_map.get_members()) {
        const char* key_str = member_info.name.c_str();
        py::set_entry(member_map, stru, sh_alloc, key_str, dict[key_str]);
    }
}

__attribute__((__visibility__("default"))) nb::object py::to_python(FieldView view,
                                                                    ToPythonMode mode) {
    if (view.empty()) { return nb::none(); }
    py::ToPythonFn to_python_fn = py::get_to_python_fn(view.get_type_hash());
    return to_python_fn(view, mode);
}

__attribute__((__visibility__("default"))) nb::object py::to_python_cast(FieldView view) {
    if (view.empty()) { return nb::none(); }
    py::ToPythonCastFn to_python_cast_fn = py::get_to_python_cast_fn(view.get_type_hash());
    return to_python_cast_fn(view);
}

__attribute__((__visibility__("default"))) void
py::from_python(FieldView view, const nb::handle& value, const std::string& field_name) {
    if (value.is_none()) { throw nb::value_error("cannot assign None to unmanaged field"); }
    if (view.empty()) { throw nb::value_error("internal error: unmanaged field is empty"); }
    STST_LOG_DEBUG() << "at field " << field_name << " of type "
                     << typing::get_type(view.get_type_hash()).name;
    auto from_python_fn = py::get_from_python_fn(view.get_type_hash());
    from_python_fn(view, value);
}

__attribute__((__visibility__("default"))) void
py::from_python(FieldAccess access, const nb::handle& value, const std::string& field_name) {
    if (value.is_none()) {
        access.clear();
        return;
    }
    if (!access.get_field().empty()) {
        STST_LOG_DEBUG() << "at field " << field_name << " of type " << typing::get_type(access.get_type_hash()).name;
        auto from_python_fn = py::get_from_python_fn(access.get_type_hash());
        from_python_fn(access, value);
    } else {
        STST_LOG_DEBUG() << "at empty field " << field_name;
        type_hash_t type_hash = py::get_stst_type(value);
        access.construct(type_hash);
        const PyType& py_type = py::get_py_types().at(type_hash);
        py_type.from_python_fn(access, value);
    }
}

__attribute__((__visibility__("default"))) nb::object py::get_entry(const MemberMap& member_map,
                                                                    StructBase& stru,
                                                                    SharedAlloc& sh_alloc,
                                                                    const std::string& name) {
    FieldView view = member_map.get_member(name, stru, sh_alloc);
    if (view.empty()) { throw nb::attribute_error(name.c_str()); }
    return to_python_cast(view);
}

__attribute__((__visibility__("default"))) nb::object py::get_entry(FieldMap& field_map,
                                                                    const std::string& name) {
    Field* field = field_map.try_get_field(name);
    if (field == nullptr) { throw nb::attribute_error(name.c_str()); }
    return to_python_cast(field->view(field_map.get_alloc()));
}

__attribute__((__visibility__("default"))) void
py::set_entry(const MemberMap& member_map, StructBase& stru, SharedAlloc& sh_alloc,
              const std::string& name, const nb::handle& value) {
    FieldView view = member_map.get_member(name, stru, sh_alloc);
    from_python(view, value, name);
}

__attribute__((__visibility__("default"))) void
py::set_entry(FieldMap& field_map, const std::string& name, const nb::handle& value) {
    STST_LOG_DEBUG() << "setting field to type " << nb::repr(value.type()).c_str();
    from_python(field_map[name], value, name);
}
