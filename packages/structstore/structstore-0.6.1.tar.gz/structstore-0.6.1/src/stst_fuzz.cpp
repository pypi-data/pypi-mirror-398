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

#include <iostream>
#include <random>
#include <string>

#include <structstore/structstore.hpp>

namespace stst = structstore;

static std::mt19937_64 suffix_rnd{stst::generate_rnd_seed()};

int structstore::stst_fuzz(std::string line) {
    if (line.size() > 2048) {
        // prevent stack overflow due to nested StructStore instances
        return -1;
    }
    std::vector<stst::StructStore> stores;
    int suffix = suffix_rnd();
    auto filename = "/shstore_fuzzed" + std::to_string(suffix);
    stst::FieldMap* fields = nullptr;
    for (char c: line) {
        std::cout << "performing fuzz action '" << c << "' ..." << std::endl;
        switch (c) {
            case 's':
                if (stores.size() >= 4) { return -1; }
                stores.emplace_back(filename);
                break;
            case 'S':
                if (stores.empty()) { return -1; }
                stores.pop_back();
                fields = nullptr;
                break;
            case 'b':
                if (stores.empty()) { return -1; }
                fields = &*stores.back();
                break;
            case 'i':
                if (!fields) { return -1; }
                fields->get<int>("i") = 5;
                break;
            case 't':
                if (!fields) { return -1; }
                fields = &fields->substore("t");
                break;
            case 'r':
                if (!fields) { return -1; }
                fields->substore("t");
                fields->remove("t");
                break;
            case 'l':
                if (!fields) { return -1; }
                fields->read_lock_();
                break;
            case 'L':
                if (!fields) { return -1; }
                fields->read_unlock_();
                break;
            case 'w':
                if (!fields) { return -1; }
                fields->write_lock_();
                break;
            case 'W':
                if (!fields) { return -1; }
                fields->write_unlock_();
                break;
            case 'c':
                if (!fields) { return -1; }
                fields->check();
                break;
            default:
                return -1;
        }
    }
    return 0;
}
