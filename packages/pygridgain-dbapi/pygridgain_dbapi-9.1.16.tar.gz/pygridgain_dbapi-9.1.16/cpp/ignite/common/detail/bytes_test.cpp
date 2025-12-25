/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "bytes.h"

#include <gtest/gtest.h>

#include <array>

using namespace ignite::detail;

TEST(bytes, swapXX) {
    EXPECT_EQ(0x0201, bytes::swap16(0x0102));
    EXPECT_EQ(0x04030201, bytes::swap32(0x01020304));
    EXPECT_EQ(0x0807060504030201, bytes::swap64(0x0102030405060708));
}

TEST(bytes, everse) {
    {
        std::int8_t x = 0x01;
        EXPECT_EQ(0x01, bytes::reverse(x));
    }
    {
        std::uint8_t x = 0x01;
        EXPECT_EQ(0x01, bytes::reverse(x));
    }
    {
        std::int16_t x = 0x0102;
        EXPECT_EQ(0x0201, bytes::reverse(x));
    }
    {
        std::uint16_t x = 0x0102;
        EXPECT_EQ(0x0201, bytes::reverse(x));
    }
    {
        std::int32_t x = 0x01020304;
        EXPECT_EQ(0x04030201, bytes::reverse(x));
    }
    {
        std::uint32_t x = 0x01020304;
        EXPECT_EQ(0x04030201, bytes::reverse(x));
    }
    {
        std::int64_t x = 0x0102030405060708;
        EXPECT_EQ(0x0807060504030201, bytes::reverse(x));
    }
    {
        std::uint64_t x = 0x0102030405060708;
        EXPECT_EQ(0x0807060504030201, bytes::reverse(x));
    }
}

TEST(bytes, adjustOrder) {
    using namespace bytes;

    {
        std::int8_t x = 0x01;
        EXPECT_EQ(x, ltob(x));
        EXPECT_EQ(x, btol(x));
        EXPECT_EQ(x, ltoh(x));
        EXPECT_EQ(x, htol(x));
        EXPECT_EQ(x, btoh(x));
        EXPECT_EQ(x, htob(x));
    }
    {
        std::int16_t x = 0x0102;
        std::int16_t y = 0x0201;
        EXPECT_EQ(y, ltob(x));
        EXPECT_EQ(y, btol(x));
        if (is_little_endian_platform()) {
            EXPECT_EQ(x, ltoh(x));
            EXPECT_EQ(x, htol(x));
            EXPECT_EQ(y, btoh(x));
            EXPECT_EQ(y, htob(x));
        } else if (is_big_endian_platform()) {
            EXPECT_EQ(y, ltoh(x));
            EXPECT_EQ(y, htol(x));
            EXPECT_EQ(x, btoh(x));
            EXPECT_EQ(x, htob(x));
        }
    }
    {
        std::int32_t x = 0x01020304;
        std::int32_t y = 0x04030201;
        EXPECT_EQ(y, ltob(x));
        EXPECT_EQ(y, btol(x));
        if (is_little_endian_platform()) {
            EXPECT_EQ(x, ltoh(x));
            EXPECT_EQ(x, htol(x));
            EXPECT_EQ(y, btoh(x));
            EXPECT_EQ(y, htob(x));
        } else if (is_big_endian_platform()) {
            EXPECT_EQ(y, ltoh(x));
            EXPECT_EQ(y, htol(x));
            EXPECT_EQ(x, btoh(x));
            EXPECT_EQ(x, htob(x));
        }
    }
    {
        std::int64_t x = 0x0102030405060708;
        std::int64_t y = 0x0807060504030201;
        EXPECT_EQ(y, ltob(x));
        EXPECT_EQ(y, btol(x));
        if (is_little_endian_platform()) {
            EXPECT_EQ(x, ltoh(x));
            EXPECT_EQ(x, htol(x));
            EXPECT_EQ(y, btoh(x));
            EXPECT_EQ(y, htob(x));
        } else if (is_big_endian_platform()) {
            EXPECT_EQ(y, ltoh(x));
            EXPECT_EQ(y, htol(x));
            EXPECT_EQ(x, btoh(x));
            EXPECT_EQ(x, htob(x));
        }
    }
}

TEST(bytes, awAccess) {
    using namespace bytes;

    {
        std::int8_t x = 0x01;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};

        store_raw(buf.data(), x);
        EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));

        auto y = load_raw<decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int16_t x = 0x0102;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};

        store_raw(buf.data(), x);
        if (is_little_endian_platform()) {
            EXPECT_EQ(0x02, std::to_integer<char>(buf[0]));
            EXPECT_EQ(0x01, std::to_integer<char>(buf[1]));
        } else if (is_big_endian_platform()) {
            EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));
            EXPECT_EQ(0x02, std::to_integer<char>(buf[1]));
        }

        auto y = load_raw<decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int32_t x = 0x01020304;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};

        store_raw(buf.data(), x);
        if (is_little_endian_platform()) {
            EXPECT_EQ(0x04, std::to_integer<char>(buf[0]));
            EXPECT_EQ(0x03, std::to_integer<char>(buf[1]));
            EXPECT_EQ(0x02, std::to_integer<char>(buf[2]));
            EXPECT_EQ(0x01, std::to_integer<char>(buf[3]));
        } else if (is_big_endian_platform()) {
            EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));
            EXPECT_EQ(0x02, std::to_integer<char>(buf[1]));
            EXPECT_EQ(0x03, std::to_integer<char>(buf[2]));
            EXPECT_EQ(0x04, std::to_integer<char>(buf[3]));
        }

        auto y = load_raw<decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int64_t x = 0x0102030405060708;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};

        store_raw(buf.data(), x);
        if (is_little_endian_platform()) {
            EXPECT_EQ(0x08, std::to_integer<char>(buf[0]));
            EXPECT_EQ(0x07, std::to_integer<char>(buf[1]));
            EXPECT_EQ(0x06, std::to_integer<char>(buf[2]));
            EXPECT_EQ(0x05, std::to_integer<char>(buf[3]));
            EXPECT_EQ(0x04, std::to_integer<char>(buf[4]));
            EXPECT_EQ(0x03, std::to_integer<char>(buf[5]));
            EXPECT_EQ(0x02, std::to_integer<char>(buf[6]));
            EXPECT_EQ(0x01, std::to_integer<char>(buf[7]));
        } else if (is_big_endian_platform()) {
            EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));
            EXPECT_EQ(0x02, std::to_integer<char>(buf[1]));
            EXPECT_EQ(0x03, std::to_integer<char>(buf[2]));
            EXPECT_EQ(0x04, std::to_integer<char>(buf[3]));
            EXPECT_EQ(0x05, std::to_integer<char>(buf[4]));
            EXPECT_EQ(0x06, std::to_integer<char>(buf[5]));
            EXPECT_EQ(0x07, std::to_integer<char>(buf[6]));
            EXPECT_EQ(0x08, std::to_integer<char>(buf[7]));
        }

        auto y = load_raw<decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
}

TEST(bytes, genericAccess) {
    using namespace bytes;

    {
        std::int8_t x = 0x01;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};
        constexpr auto E = endian::LITTLE;

        store<E>(buf.data(), x);
        EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));

        auto y = load<E, decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int8_t x = 0x01;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};
        constexpr auto E = endian::BIG;

        store<E>(buf.data(), x);
        EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));

        auto y = load<E, decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int16_t x = 0x0102;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};
        constexpr auto E = endian::LITTLE;

        store<E>(buf.data(), x);
        EXPECT_EQ(0x02, std::to_integer<char>(buf[0]));
        EXPECT_EQ(0x01, std::to_integer<char>(buf[1]));

        auto y = load<E, decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int16_t x = 0x0102;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};
        constexpr auto E = endian::BIG;

        store<E>(buf.data(), x);
        EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));
        EXPECT_EQ(0x02, std::to_integer<char>(buf[1]));

        auto y = load<E, decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int32_t x = 0x01020304;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};
        constexpr auto E = endian::LITTLE;

        store<E>(buf.data(), x);
        EXPECT_EQ(0x04, std::to_integer<char>(buf[0]));
        EXPECT_EQ(0x03, std::to_integer<char>(buf[1]));
        EXPECT_EQ(0x02, std::to_integer<char>(buf[2]));
        EXPECT_EQ(0x01, std::to_integer<char>(buf[3]));

        auto y = load<E, decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int32_t x = 0x01020304;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};
        constexpr auto E = endian::BIG;

        store<E>(buf.data(), x);
        EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));
        EXPECT_EQ(0x02, std::to_integer<char>(buf[1]));
        EXPECT_EQ(0x03, std::to_integer<char>(buf[2]));
        EXPECT_EQ(0x04, std::to_integer<char>(buf[3]));

        auto y = load<E, decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int64_t x = 0x0102030405060708;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};
        constexpr auto E = endian::LITTLE;

        store<E>(buf.data(), x);
        EXPECT_EQ(0x08, std::to_integer<char>(buf[0]));
        EXPECT_EQ(0x07, std::to_integer<char>(buf[1]));
        EXPECT_EQ(0x06, std::to_integer<char>(buf[2]));
        EXPECT_EQ(0x05, std::to_integer<char>(buf[3]));
        EXPECT_EQ(0x04, std::to_integer<char>(buf[4]));
        EXPECT_EQ(0x03, std::to_integer<char>(buf[5]));
        EXPECT_EQ(0x02, std::to_integer<char>(buf[6]));
        EXPECT_EQ(0x01, std::to_integer<char>(buf[7]));

        auto y = load<E, decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
    {
        std::int64_t x = 0x0102030405060708;
        std::array<std::byte, sizeof(x)> buf{std::byte{0}};
        constexpr auto E = endian::BIG;

        store<E>(buf.data(), x);
        EXPECT_EQ(0x01, std::to_integer<char>(buf[0]));
        EXPECT_EQ(0x02, std::to_integer<char>(buf[1]));
        EXPECT_EQ(0x03, std::to_integer<char>(buf[2]));
        EXPECT_EQ(0x04, std::to_integer<char>(buf[3]));
        EXPECT_EQ(0x05, std::to_integer<char>(buf[4]));
        EXPECT_EQ(0x06, std::to_integer<char>(buf[5]));
        EXPECT_EQ(0x07, std::to_integer<char>(buf[6]));
        EXPECT_EQ(0x08, std::to_integer<char>(buf[7]));

        auto y = load<E, decltype(x)>(buf.data());
        EXPECT_EQ(x, y);
    }
}

TEST(bytes, genericAccessFloat) {
    using namespace bytes;

    {
        float x = 0.1234f;
        std::array<std::byte, sizeof(x)> buf1{std::byte{0}};
        std::array<std::byte, sizeof(x)> buf2{std::byte{0}};
        constexpr auto E1 = endian::LITTLE;
        constexpr auto E2 = endian::BIG;

        store<E1>(buf1.data(), x);
        store<E2>(buf2.data(), x);
        for (std::size_t i = 0; i < sizeof(x); i++) {
            EXPECT_EQ(std::to_integer<char>(buf1[i]), std::to_integer<char>(buf2[sizeof(x) - i - 1]));
        }

        auto y1 = load<E1, decltype(x)>(buf1.data());
        auto y2 = load<E2, decltype(x)>(buf2.data());
        EXPECT_EQ(x, y1);
        EXPECT_EQ(x, y2);
    }
    {
        double x = 0.1234;
        std::array<std::byte, sizeof(x)> buf1{std::byte{0}};
        std::array<std::byte, sizeof(x)> buf2{std::byte{0}};
        constexpr auto E1 = endian::LITTLE;
        constexpr auto E2 = endian::BIG;

        store<E1>(buf1.data(), x);
        store<E2>(buf2.data(), x);
        for (std::size_t i = 0; i < sizeof(x); i++) {
            EXPECT_EQ(std::to_integer<char>(buf1[i]), std::to_integer<char>(buf2[sizeof(x) - i - 1]));
        }

        auto y1 = load<E1, decltype(x)>(buf1.data());
        auto y2 = load<E2, decltype(x)>(buf2.data());
        EXPECT_EQ(x, y1);
        EXPECT_EQ(x, y2);
    }
}

TEST(bytes, rotate_left64) {
    using namespace bytes;

    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 0), 0x0123456776543210ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 1), 0x02468ACEECA86420ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 2), 0x048D159DD950C840ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 3), 0x91A2B3BB2A19080ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 4), 0x1234567765432100ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 5), 0x2468ACEECA864200ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 6), 0x48D159DD950C8400ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 7), 0x91A2B3BB2A190800ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 8), 0x2345677654321001ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 12), 0x3456776543210012ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 16), 0x4567765432100123ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 20), 0x5677654321001234ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 24), 0x6776543210012345ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 28), 0x7765432100123456ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 32), 0x7654321001234567ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 36), 0x6543210012345677ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 40), 0x5432100123456776ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 44), 0x4321001234567765ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 48), 0x3210012345677654ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 52), 0x2100123456776543ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 56), 0x1001234567765432ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 60), 0x0012345677654321ULL);
    EXPECT_EQ(rotate_left64(0x0123456776543210ULL, 64), 0x0123456776543210ULL);
}
