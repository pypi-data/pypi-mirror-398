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

#ifndef STST_PY_HPP
#define STST_PY_HPP

#include "structstore/stst_alloc.hpp"
#include "structstore/stst_callstack.hpp"
#include "structstore/stst_field.hpp"
#include "structstore/stst_fieldmap.hpp"
#include "structstore/stst_membermap.hpp"
#include "structstore/stst_struct.hpp"
#include "structstore/stst_structstore.hpp"
#include "structstore/stst_typing.hpp"
#include "structstore/stst_utils.hpp"

#include <functional>
#include <sstream>
#include <stdexcept>
#include <type_traits>
#include <typeinfo>
#include <unordered_map>

#include <nanobind/make_iterator.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

// make customized STL containers opaque to nanobind
namespace nanobind::detail {
template<class T>
class type_caster<structstore::shr_vector<T>>
    : public type_caster_base<structstore::shr_vector<T>> {};
} // namespace nanobind::detail

namespace structstore {

namespace nb = nanobind;

class py {
public:
    enum class ToPythonMode {
        NON_RECURSIVE,
        RECURSIVE,
    };

    using FromPythonFn = std::function<void(FieldView, SharedAlloc&, const nb::handle&)>;
    using ToPythonFn = std::function<nb::object(FieldView, ToPythonMode mode)>;
    using ToPythonCastFn = std::function<nb::object(FieldView)>;

    __attribute__((__visibility__("default"))) static nb::object SimpleNamespace;

private:
    struct __attribute__((__visibility__("default"))) PyType {
        const FromPythonFn from_python_fn;
        const ToPythonFn to_python_fn;
        const ToPythonCastFn to_python_cast_fn;
    };

    static std::unordered_map<type_hash_t, const PyType>& get_py_types();
    static std::unordered_map<std::string, type_hash_t>& get_typemap();

    static const PyType& get_py_type(type_hash_t type_hash);
    static type_hash_t get_stst_type(const nb::handle& value);

    // get Struct member or FieldMap field
    static nb::object get_entry(StructBase& stru, const std::string& name);
    static nb::object get_entry(FieldMap& field_map, const std::string& name);
    // set Struct member or FieldMap field
    static void set_entry(StructBase& stru, const std::string& name, const nb::handle& value);
    static void set_entry(FieldMap& field_map, const std::string& name, const nb::handle& value);
    // FieldMap fields or Struct members
    static nb::object entries_to_python(FieldMap& field_map, py::ToPythonMode mode);
    static nb::object entries_to_python(StructBase& stru, py::ToPythonMode mode);
    // FieldMap fields or Struct members
    static void entries_from_python(FieldMap& field_map, const nb::handle& value);
    static void entries_from_python(StructBase& stru, const nb::handle& value);

public:
    template<typename T>
    static void throw_convert_error(const nb::handle& value) {
        std::ostringstream msg;
        msg << "failed to convert " << nb::repr(value.type()).c_str() << " to " << typeid(T).name();
        Callstack::throw_with_trace(msg.str());
    }

    template<typename W, typename W_py>
    static void default_from_python_fn(FieldView view, SharedAlloc&, const nb::handle& value) {
        using T = unwrap_type_t<W>;
        if (!nb::isinstance<T>(value)) { throw_convert_error<T>(value); }
        const W& w = nb::cast<W>(value, false);
        view.get<T>() = unwrap<W>(w);
    }

    template<typename W, typename W_py>
    static nb::object default_to_python_fn(FieldView view, ToPythonMode) {
        using T = unwrap_type_t<W>;
        return W_py(ref_wrap(view.get<T>()));
    }

    template<typename W>
    static nb::object default_to_python_cast_fn(FieldView view) {
        using T = unwrap_type_t<W>;
        return nb::cast(ref_wrap(view.get<T>()), nb::rv_policy::reference);
    }

    template<typename W>
    static void register_type(FromPythonFn from_python_fn, ToPythonFn to_python_fn,
                              ToPythonCastFn to_python_cast_fn = default_to_python_cast_fn<W>) {
        static_assert(std::is_same_v<W, std::remove_const_t<W>>);
        static_assert(std::is_same_v<W, std::remove_reference_t<W>>);
        // check that a wrapper type (or String) is provided:
        static_assert(std::is_same_v<std::remove_reference_t<wrap_type_w<W>>, W>);
        using T = unwrap_type_t<W>;
        static_assert(typing::is_field_type<unwrap_type_t<W>>);

        PyType py_type{from_python_fn, to_python_fn, to_python_cast_fn};
        const type_hash_t type_hash = typing::get_type_hash<T>();
        STST_LOG_DEBUG() << "registering Python type '" << typing::get_type<T>().name
                         << "', wrapper type '" << typeid(W).name() << "' with hash '" << type_hash
                         << "'";
        bool inserted = get_py_types().insert({type_hash, py_type}).second;
        if (!inserted) {
            std::ostringstream str;
            str << "Python type already registered: " << typing::get_type<T>().name;
            throw std::runtime_error(str.str());
        }
    }

    template<typename T>
    static void add_compatible_type(std::string type_name) {
        const type_hash_t type_hash = typing::get_type_hash<T>();
        STST_LOG_DEBUG() << "registering compatible type " << type_name << " for "
                         << typeid(T).name();
        bool inserted = get_typemap().insert({type_name, type_hash}).second;
        if (!inserted) {
            std::ostringstream str;
            str << "compatible Python type already registered: " << type_name;
            throw std::runtime_error(str.str());
        }
    }

    template<typename W>
    static void map_from_python_fn(FieldView view, SharedAlloc&, const nb::handle& value) {
        using T = unwrap_type_t<W>;
        if (py::copy_cast_from_python<W>(view, value)) { return; }
        T& map = view.get<T>();
        if (nb::hasattr(value, "__dict__")) {
            entries_from_python(map, nb::dict(value.attr("__dict__")));
        } else {
            entries_from_python(map, value);
        }
    }

    template<typename W>
    static nb::object map_to_python_fn(FieldView view, ToPythonMode mode) {
        using T = unwrap_type_t<W>;
        auto& map = view.get<T>();
        return py::entries_to_python(map, mode);
    }

    template<typename W>
    static void register_struct_ptr_type() {
        using T = unwrap_type_t<W>;
        static_assert(!std::is_pointer_v<T>);
        static_assert(std::is_class_v<T>);
        auto from_python_fn = [](FieldView view, SharedAlloc& sh_alloc, const nb::handle& value) {
            if (!nb::isinstance<W>(value)) { throw_convert_error<T>(value); }
            W& w = nb::cast<W&>(value, false);
            T& t = unwrap(w);
            if (!sh_alloc.is_owned(&t)) {
                Callstack::throw_with_trace("cannot assign pointer to different memory region");
            }
            view.get<OffsetPtr<T>>() = &t;
        };
        py::ToPythonFn to_python_fn = [](FieldView view, py::ToPythonMode mode) {
            T* t_ptr = view.get<OffsetPtr<T>>().get();
            if (t_ptr == nullptr) { return nb::none(); }
            StructBase& stru = *t_ptr;
            return entries_to_python(stru, mode);
        };
        py::ToPythonCastFn to_python_cast_fn = [](FieldView view) {
            T* t_ptr = view.get<OffsetPtr<T>>().get();
            if (t_ptr == nullptr) { return nb::none(); }
            return nb::cast(ref_wrap(*t_ptr), nb::rv_policy::reference);
        };
        register_type<OffsetPtr<T>>(from_python_fn, to_python_fn, to_python_cast_fn);
    }

    template<typename W>
    static void register_struct_type(nb::class_<W>& cls) {
        using T = unwrap_type_t<W>;
        static_assert(std::is_base_of_v<Struct<T>, T>);
        static_assert(std::is_same_v<T, std::remove_cv_t<T>>);
        static_assert(std::is_same_v<typename T::Ref, W>);
        cls.def("__init__",
                [](typename T::Ref* struct_ref) { T::Ref::create_in_place(struct_ref); });
        py::ToPythonFn to_python_fn = [](FieldView view, py::ToPythonMode mode) {
            Struct<T>& t = view.get<T>();
            StructBase& stru = t;
            return entries_to_python(stru, mode);
        };
        auto from_python_fn = [](FieldView view, SharedAlloc&, const nb::handle& value) {
            if (py::copy_cast_from_python<W>(view, value)) { return; }
            nb::dict dict;
            bool is_dict = false;
            if (nb::hasattr(value, "__dict__")) {
                dict = nb::dict(value.attr("__dict__"));
                is_dict = true;
            }
            if (nb::isinstance<nb::dict>(value)) {
                dict = nb::cast<nb::dict>(value);
                is_dict = true;
            }
            if (!is_dict) { throw_convert_error<T>(value); }
            T& t = view.get<T>();
            entries_from_python(t, dict);
        };
        register_type<W>(from_python_fn, to_python_fn);
        add_compatible_type<T>(nb::repr(cls).c_str());
        register_struct_ptr_type<W>();
        register_map_funcs<W>(cls);

        cls.def("__getstate__", [](W& w) {
            CallstackEntry entry{"py::__getstate__()"};
            nb::object obj = entries_to_python(unwrap(w), py::ToPythonMode::RECURSIVE);
            return obj;
        });

        cls.def("__dir__", [](W& w) {
            nb::list slots;
            for (const MemberInfo& member_info: unwrap(w).get_member_map().get_members()) {
                slots.append(nb::str(member_info.name.c_str()));
            }
            return slots;
        });
    }

    static const FromPythonFn& get_from_python_fn(type_hash_t type_hash) {
        return get_py_type(type_hash).from_python_fn;
    }

    static const ToPythonFn& get_to_python_fn(type_hash_t type_hash) {
        return get_py_type(type_hash).to_python_fn;
    }

    static const ToPythonCastFn& get_to_python_cast_fn(type_hash_t type_hash) {
        return get_py_type(type_hash).to_python_cast_fn;
    }

    template<typename W>
    static void register_basic_ptr_type() {
        using T = unwrap_type_t<W>;
        static_assert(std::is_same_v<T, W>);
        static_assert(!std::is_pointer_v<T>);
        static_assert(!std::is_class_v<T>);
        auto from_python_fn = [](FieldView view, SharedAlloc&, const nb::handle& value) {
            if (!nb::isinstance<T>(value)) { throw_convert_error<T>(value); }
            T t = nb::cast<T>(value, false);
            *view.get<OffsetPtr<T>>() = t;
        };
        py::ToPythonFn to_python_fn = [](FieldView view, py::ToPythonMode) {
            T* t_ptr = view.get<OffsetPtr<T>>().get();
            if (t_ptr == nullptr) { return nb::none(); }
            return nb::cast(ref_wrap(*t_ptr));
        };
        py::ToPythonCastFn to_python_cast_fn = [](FieldView view) {
            T* t_ptr = view.get<OffsetPtr<T>>().get();
            if (t_ptr == nullptr) { return nb::none(); }
            return nb::cast(ref_wrap(*t_ptr));
        };
        register_type<OffsetPtr<T>>(from_python_fn, to_python_fn, to_python_cast_fn);
    }

    template<typename W, typename W_py>
    static void register_basic_type() {
        using T = unwrap_type_t<W>;
        static_assert(std::is_same_v<T, W>);
        register_type<W>(default_from_python_fn<W, W_py>, default_to_python_fn<W, W_py>,
                         default_to_python_cast_fn<W>);
        add_compatible_type<T>(nb::repr(nb::cast<T>(T()).type()).c_str());
        register_basic_ptr_type<W>();
    }

    template<typename W>
    static void register_complex_type_funcs(nb::class_<W>& cls) {
        using T = unwrap_type_t<W>;
        static_assert(!std::is_pointer_v<T>);
        cls.def("to_yaml", [](W& w) { return YAML::Dump(FieldView{unwrap(w)}.to_yaml()); });
        cls.def("__repr__", [](W& w) {
            std::ostringstream str;
            FieldView{unwrap(w)}.to_text(str);
            return str.str();
        });
        cls.def("copy",
                [](W& w) { return to_python(FieldView{unwrap(w)}, ToPythonMode::NON_RECURSIVE); });
        cls.def("deepcopy",
                [](W& w) { return to_python(FieldView{unwrap(w)}, ToPythonMode::RECURSIVE); });
        cls.def("__copy__",
                [](W& w) { return to_python(FieldView{unwrap(w)}, ToPythonMode::NON_RECURSIVE); });
        cls.def("__deepcopy__", [](W& w, nb::handle&) {
            return to_python(FieldView{unwrap(w)}, ToPythonMode::RECURSIVE);
        });
        cls.def("__eq__", [](W& w, nb::handle& other) {
            if constexpr (std::is_same_v<T, FieldMap>) {
                if (nb::isinstance<StructStore>(other)) {
                    return unwrap(w) == *nb::cast<StructStore&>(other, false);
                }
            }
            if (const W* other_ = try_cast<W>(other)) { return unwrap(w) == unwrap(*other_); }
            return false;
        });
        cls.def("read_lock", [](W& w) { return unwrap(w).read_lock(); }, nb::rv_policy::move);
        cls.def("write_lock", [](W& w) { return unwrap(w).write_lock(); }, nb::rv_policy::move);
    }

    template<typename W>
    static W* try_cast(const nb::handle& value) {
        try {
            return &nb::cast<W&>(value, false);
        } catch (const nb::cast_error&) { return nullptr; }
    }

    template<typename W>
    static bool copy_cast_from_python(FieldView view, const nb::handle& value) {
        using T = unwrap_type_t<W>;
        // check that a wrapper type (or String) is provided:
        static_assert(std::is_same_v<std::remove_reference_t<wrap_type_w<W>>, W>);

        W* value_cpp_ptr = try_cast<W>(value);
        if (value_cpp_ptr == nullptr) { return false; }
        T& value_cpp = unwrap(*value_cpp_ptr);
        T& field_cpp = view.get<T>();
        STST_LOG_DEBUG() << "at type " << typing::get_type<T>().name;
        if (&value_cpp == &field_cpp) {
            STST_LOG_DEBUG() << "copying to itself";
            return true;
        }
        STST_LOG_DEBUG() << "copying " << typing::get_type<T>().name << " from " << &value_cpp
                         << " to " << &field_cpp;
        field_cpp = value_cpp;
        return true;
    }

    // for Struct member map and FieldMap
    template<typename W>
    static void register_map_funcs(nb::class_<W>& cls) {
        using T = unwrap_type_t<W>;
        register_complex_type_funcs<W>(cls);

        cls.def("__getstate__", [](W& w) {
            CallstackEntry entry{"py::__getstate__()"};
            nb::object obj = entries_to_python(unwrap(w), py::ToPythonMode::RECURSIVE);
            return obj;
        });

        if constexpr (std::is_base_of_v<FieldType<T>, T> && !std::is_same_v<W, StructStore>) {
            cls.def("__setstate__", [](W& w, nb::handle value) {
                CallstackEntry entry{"py::__setstate__()"};
                using T = unwrap_type_t<W>;
                static_assert(std::is_same_v<typename T::Ref, W>);
                // create temporary field to be able to call from_python()
                Field* field = static_alloc.allocate<Field>();
                new (field) Field;
                auto access = FieldAccess{*field, static_alloc, nullptr};
                // ensure that the field has the desired type T
                access.get<T>();
                from_python(access, value, "<root>");
                new (&w) typename T::Ref{std::move(*field), static_alloc};
                static_alloc.deallocate(field);
            });
        } else {
            cls.def("__setstate__", [](T&, nb::handle) {
                throw std::runtime_error("cannot unpickle type " + std::string(typeid(T).name()));
            });
        }

        cls.def(
                "__getattr__",
                [](W& w, const std::string& name) { return get_entry(unwrap(w), name); },
                nb::arg("name"));

        cls.def(
                "__setattr__",
                [](W& w, const std::string& name, const nb::handle& value) {
                    auto& val = unwrap(w);
                    auto lock = val.write_lock();
                    return set_entry(val, name, value);
                },
                nb::arg("name"), nb::arg("value").none());

        cls.def(
                "__getitem__",
                [](W& w, const std::string& name) {
                    // todo: when returning a field, there should be a read lock on the parent FieldMap
                    // => attach a read lock to the return value?
                    return get_entry(unwrap(w), name);
                },
                nb::arg("name"));

        cls.def(
                "__setitem__",
                [](W& w, const std::string& name, const nb::handle& value) {
                    auto& val = unwrap(w);
                    auto lock = val.write_lock();
                    return set_entry(val, name, value);
                },
                nb::arg("name"), nb::arg("value").none());

        cls.def("check", [](W& w) {
            STST_LOG_DEBUG() << "checking from python ...";
            w.check();
        });
    }

    template<typename W>
    static void register_field_map_funcs(nb::class_<W>& cls) {
        register_map_funcs<W>(cls);

        // query functions

        cls.def("__dir__", [](W& w) {
            nb::list slots;
            const auto& field_map = unwrap(w);
            for (shr_string_idx str_idx: field_map.get_slots()) {
                slots.append(nb::str(field_map.get_alloc().strings().get(str_idx)->c_str()));
            }
            return slots;
        });

        cls.def("__len__", [](W& w) { return unwrap(w).get_slots().size(); });

        cls.def("empty", [](W& w) { return unwrap(w).empty(); });

        // modify functions

        cls.def("clear", [](W& w) { unwrap(w).clear(); });

        cls.def(
                "__delattr__",
                [](W& w, const std::string& name) { return unwrap(w).remove(name.c_str()); },
                nb::arg("name"));

        cls.def(
                "__delitem__",
                [](W& w, const std::string& name) { return unwrap(w).remove(name.c_str()); },
                nb::arg("name"));
    }

    static nb::object to_python(FieldView view, ToPythonMode mode);

    static nb::object to_python_cast(FieldView view);

    // for unmanaged fields
    static void from_python(FieldView view, SharedAlloc& sh_alloc, const nb::handle& value,
                            const std::string& field_name);

    // for managed fields
    static void from_python(FieldAccess access, const nb::handle& value,
                            const std::string& field_name);
};

} // namespace structstore

#endif
