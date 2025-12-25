/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "detail/byte_traits.h"

#include <array>
#include <cstddef>
#include <string>
#include <string_view>
#include <vector>

namespace ignite {

/**
 * @brief Wrapper for raw bytes.
 *
 * Provides convenient methods for managing data in binary format.
 */
struct bytes_view : std::basic_string_view<std::byte, detail::byte_traits> {
    using base_type = std::basic_string_view<std::byte, detail::byte_traits>;

    constexpr bytes_view() noexcept = default;

    constexpr bytes_view(const std::byte *data, std::size_t size) noexcept
        : base_type(data, size) {}

    constexpr bytes_view(const void *data, std::size_t size) noexcept
        : base_type(static_cast<const std::byte *>(data), size) {}

    constexpr bytes_view(const base_type &v) noexcept // NOLINT(google-explicit-constructor)
        : base_type(v.data(), v.size()) {}

    template<std::size_t SIZE>
    constexpr bytes_view(const char (&v)[SIZE]) noexcept // NOLINT(google-explicit-constructor)
        : base_type(reinterpret_cast<const std::byte *>(v), SIZE) {}

    template<std::size_t SIZE>
    constexpr bytes_view(const std::array<std::byte, SIZE> &v) noexcept // NOLINT(google-explicit-constructor)
        : base_type(v.data(), v.size()) {}

    bytes_view(const std::string &v) noexcept // NOLINT(google-explicit-constructor)
        : base_type(reinterpret_cast<const std::byte *>(v.data()), v.size()) {}

    bytes_view(const std::string_view &v) noexcept // NOLINT(google-explicit-constructor)
        : base_type(reinterpret_cast<const std::byte *>(v.data()), v.size()) {}

    bytes_view(const std::vector<std::byte> &v) noexcept // NOLINT(google-explicit-constructor)
        : base_type(v.data(), v.size()) {}

    explicit operator std::string() const { return {reinterpret_cast<const char *>(data()), size()}; }

    explicit operator std::vector<std::byte>() const { return {begin(), end()}; }
};

} // namespace ignite
