/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "hash_utils.h"

#include <assert.h>

#include "bytes.h"

namespace ignite::detail {

namespace {
constexpr std::uint64_t C1 = 0x87c37b91114253d5L;
constexpr std::uint64_t C2 = 0x4cf5ad432745937fL;
constexpr std::int32_t R1 = 31;
constexpr std::int32_t R2 = 27;
constexpr std::int32_t R3 = 33;
constexpr std::int32_t M = 5;
constexpr std::int32_t N1 = 0x52dce729;
constexpr std::int32_t N2 = 0x38495ab5;

constexpr std::uint64_t fmix64(std::uint64_t hash)
{
    hash ^= hash >> 33;
    hash *= 0xff51afd7ed558ccdL;
    hash ^= hash >> 33;
    hash *= 0xc4ceb9fe1a85ec53L;
    hash ^= hash >> 33;

    return hash;
}

std::int64_t hash64_internal(bytes_view data, std::uint64_t seed) noexcept {
    std::uint64_t h1 = seed;
    std::uint64_t h2 = seed;
    std::uint64_t length = std::uint64_t(data.size());
    std::uint64_t nblocks = length >> 4;

    // body
    for (std::uint64_t i = 0; i < nblocks; i++)
    {
        std::uint64_t idx = (i << 4);
        std::uint64_t kk1 = bytes::load<endian::LITTLE, std::uint64_t>(data.data() + idx);
        std::uint64_t kk2 = bytes::load<endian::LITTLE, std::uint64_t>(data.data() + idx + 8);

        // mix functions for k1
        kk1 *= C1;
        kk1 = std::uint64_t(bytes::rotate_left64(kk1, R1));
        kk1 *= C2;
        h1 ^= kk1;
        h1 = std::uint64_t(bytes::rotate_left64(h1, R2));
        h1 += h2;
        h1 = h1 * M + N1;

        // mix functions for k2
        kk2 *= C2;
        kk2 = std::uint64_t(bytes::rotate_left64(kk2, R3));
        kk2 *= C1;
        h2 ^= kk2;
        h2 = std::uint64_t(bytes::rotate_left64(h2, R1));
        h2 += h1;
        h2 = h2 * M + N2;
    }

    // tail
    std::uint64_t k1 = 0;
    std::uint64_t k2 = 0;
    std::uint64_t index = nblocks << 4;
    switch (length - index)
    {
        case 15:
            k2 ^= (std::uint64_t(data[index + 14]) & 0xff) << 48;
            // Fallthrough
        case 14:
            k2 ^= (std::uint64_t(data[index + 13]) & 0xff) << 40;
            // Fallthrough
        case 13:
            k2 ^= (std::uint64_t(data[index + 12]) & 0xff) << 32;
            // Fallthrough
        case 12:
            k2 ^= (std::uint64_t(data[index + 11]) & 0xff) << 24;
            // Fallthrough
        case 11:
            k2 ^= (std::uint64_t(data[index + 10]) & 0xff) << 16;
            // Fallthrough
        case 10:
            k2 ^= (std::uint64_t(data[index + 9]) & 0xff) << 8;
            // Fallthrough

        case 9:
            k2 ^= std::uint64_t(data[index + 8]) & 0xff;
            k2 *= C2;
            k2 = std::uint64_t(bytes::rotate_left64(k2, R3));
            k2 *= C1;
            h2 ^= k2;
            // Fallthrough

        case 8:
            k1 ^= (std::uint64_t(data[index + 7]) & 0xff) << 56;
            // Fallthrough
        case 7:
            k1 ^= (std::uint64_t(data[index + 6]) & 0xff) << 48;
            // Fallthrough
        case 6:
            k1 ^= (std::uint64_t(data[index + 5]) & 0xff) << 40;
            // Fallthrough
        case 5:
            k1 ^= (std::uint64_t(data[index + 4]) & 0xff) << 32;
            // Fallthrough
        case 4:
            k1 ^= (std::uint64_t(data[index + 3]) & 0xff) << 24;
            // Fallthrough
        case 3:
            k1 ^= (std::uint64_t(data[index + 2]) & 0xff) << 16;
            // Fallthrough
        case 2:
            k1 ^= (std::uint64_t(data[index + 1]) & 0xff) << 8;
            // Fallthrough

        case 1:
            k1 ^= std::uint64_t(data[index]) & 0xff;
            k1 *= C1;
            k1 = std::uint64_t(bytes::rotate_left64(k1, R1));
            k1 *= C2;
            h1 ^= k1;
            // Fallthrough

        case 0:
            break;

        default:
            // Unreachable
            assert(false);
    }

    // finalization
    h1 ^= length;
    h2 ^= length;

    h1 += h2;
    h2 += h1;

    h1 = fmix64(h1);
    h2 = fmix64(h2);

    return h1 + h2;
}

/**
 * Generates 64-bit hash from the integer value and seed.
 *
 * @param data The input integer value.
 * @param seed The initial seed value.
 * @return The 64-bit hash.
 */
std::uint64_t hash_internal(std::int32_t data, std::uint64_t seed) {
    std::uint64_t h1 = seed;
    std::uint64_t h2 = seed;

    std::uint64_t k1 = 0;

    k1 ^= data & 0xffffffffL;
    k1 *= C1;
    k1 = std::uint64_t(bytes::rotate_left64(k1, R1));
    k1 *= C2;
    h1 ^= k1;

    // finalization
    h1 ^= 4;
    h2 ^= 4;

    h1 += h2;
    h2 += h1;

    h1 = fmix64(h1);
    h2 = fmix64(h2);

    return h1 + h2;
}

/**
 * Generates 32-bit hash from the integer value.
 *
 * @param data The input integer value.
 * @param seed Seed.
 * @return The 32-bit hash.
 */
std::int32_t hash32_internal(std::int32_t data, std::int32_t seed) {
    std::uint64_t hash = hash_internal(data, seed);

    return std::int32_t(hash ^ (hash >> 32));
}

} // anonymous namespace

std::int32_t hash32_internal(bytes_view data, std::uint64_t seed) noexcept {
    auto hash64 = hash64_internal(data, seed);

    return static_cast<std::int32_t>(hash64 ^ (hash64 >> 32));
}

std::int32_t hash32(bytes_view data) noexcept {
    return data.empty() ? 0 : hash32_internal(data, 0);
}

std::int32_t hash_combine(std::int32_t h1, std::int32_t h2) noexcept {
    return hash32_internal(h1, h2);
}

} // namespace ignite::detail
