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

#include "structstore/stst_mmap.hpp"
#include "structstore/stst_callstack.hpp"
#include "structstore/stst_utils.hpp"
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <sys/mman.h>
#include <unistd.h>
#include <unordered_map>

using namespace structstore;

MmapHelper::MmapHelper(int fd, void* sh_data_ptr)
    : fd{fd}, sh_data_ptr{sh_data_ptr}, size{*(size_t*) sh_data_ptr} {}

std::unique_ptr<MmapHelper> MmapHelper::mmap_new_fd(int fd, size_t size) {
    // set size of shared mem or file
    ssize_t result = ftruncate(fd, size);
    if (result < 0) { throw std::runtime_error("reserving shared memory failed"); }

    // store size
    result = write(fd, &size, sizeof(size_t));
    lseek(fd, 0, SEEK_SET);
    if (result != sizeof(size_t)) { throw std::runtime_error("writing initial size failed"); }

    return mmap_existing_fd(fd);
}

std::unique_ptr<MmapHelper> MmapHelper::mmap_existing_fd(int fd) {
    // map memory
    void* sh_data_ptr = mmap(nullptr, max_mmap_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (sh_data_ptr == MAP_FAILED) { throw std::runtime_error("mmap'ing existing memory failed"); }
    stst_assert((std::ptrdiff_t) sh_data_ptr % 8 == 0);

    return std::make_unique<MmapHelper>(fd, sh_data_ptr);
}

MmapHelper::~MmapHelper() {
    stst_assert(sh_data_ptr);
    munmap(sh_data_ptr, size);
    sh_data_ptr = nullptr;
}

void MmapHelper::change_size(ssize_t sizediff) {
    stst_assert(size + sizediff < max_mmap_size);
    STST_LOG_DEBUG() << "resizing from " << size << " to " << size + sizediff << " bytes";
    size += sizediff;
    ssize_t result = ftruncate(fd, size);
    if (result < 0) { throw std::runtime_error("resizing memory mapping failed"); }
}