#include <array>
#include <cmath>
#include <iostream>

using namespace std;

int uint64_log2(uint64_t n) {
#define S(k)                                                                                       \
    if (n >= (UINT64_C(1) << k)) {                                                                 \
        i += k;                                                                                    \
        n >>= k;                                                                                   \
    }
    int i = -(n == 0);
    S(32);
    S(16);
    S(8);
    S(4);
    S(2);
    S(1);
    return i;
#undef S
}

int index(uint64_t size) {
    size = size <= 3 ? 3 : size;
    if (size > (1ull << 21)) { return 59; }
    return uint64_log2(size * size * size - 1ull) - 4ull;
}

int main() {
    std::array<uint32_t, 65> sizes;
    for (uint64_t bits = 1; bits <= 64; ++bits) {
        uint64_t size = (uint64_t) (std::pow(2, bits / 3.0) + 0.001);
        int idx = index(size);
        sizes[idx] = size;
        std::cout << size << " at index " << idx << std::endl;
    }
    //    std::cout << "no bits at index " << index(0) << std::endl;
    //    for (uint64_t bits = 0; bits <= 32; ++bits) {
    //        std::cout << bits << " bits at index " << index(1ull << bits) << std::endl;
    //    }
    for (uint64_t i = 1; i <= (1ull << 30); ++i) {
        int idx = index(i);
        uint64_t size = sizes[idx];
        if (size >= i && (size < 4 || size < i * 1.5)) continue;
        std::cout << i << ": " << size << ", " << idx << std::endl;
        break;
    }
    return 0;
}
