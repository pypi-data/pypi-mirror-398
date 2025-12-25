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

#ifndef STST_MMAP_HPP
#define STST_MMAP_HPP

#include <cstddef>
#include <memory>
#include <sys/types.h>
#include <utility>

namespace structstore {

class MmapHelper {
public:
#ifdef STRUCTSTORE_EXTRALARGE
    static constexpr size_t max_mmap_size = 8ull * 1024ull * 1024ull * 1024ull; // 8GB
#else
    static constexpr size_t max_mmap_size = 8ull * 1024ull * 1024ull * 1024ull; // 8GB
#endif

protected:
    int fd;
    void* sh_data_ptr;
    size_t& size;

    MmapHelper() = delete;
    MmapHelper(const MmapHelper&) = delete;
    MmapHelper& operator=(const MmapHelper&) = delete;
    MmapHelper(MmapHelper&& other) = delete;

public:
    MmapHelper(int fd, void* sh_data_ptr);

    static std::unique_ptr<MmapHelper> mmap_new_fd(int fd, size_t size);

    static std::unique_ptr<MmapHelper> mmap_existing_fd(int fd);

    MmapHelper& operator=(MmapHelper&& other) noexcept {
        std::swap(fd, other.fd);
        std::swap(size, other.size);
        std::swap(sh_data_ptr, other.sh_data_ptr);
        return *this;
    }

    ~MmapHelper();

    inline const void* get_data() const { return sh_data_ptr; }

    inline size_t get_size() const { return size; }

    void change_size(ssize_t sizediff);
};

} // namespace structstore

#endif
