/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <cstdint>
#include <string>

namespace ignite {

template<typename T>
T *get_pointer_with_offset(T *ptr, size_t offset) {
    auto *ptr_bytes = reinterpret_cast<std::uint8_t *>(ptr);
    return (T *) (ptr_bytes + offset);
}

/**
 * Copy string to buffer of the specific length.
 *
 * @param str String to copy data from.
 * @param buf Buffer to copy data to.
 * @param buffer_len Length of the buffer.
 * @return Length of the resulting string in buffer.
 */
size_t copy_string_to_buffer(const std::string &str, char *buf, std::size_t buffer_len);

/**
 * Convert SQL string buffer to std::string.
 *
 * @param sql_str SQL string buffer.
 * @param sql_str_len SQL string length.
 * @return Standard string containing the same data.
 */
std::string sql_string_to_string(const unsigned char *sql_str, std::int32_t sql_str_len);

} // namespace ignite
