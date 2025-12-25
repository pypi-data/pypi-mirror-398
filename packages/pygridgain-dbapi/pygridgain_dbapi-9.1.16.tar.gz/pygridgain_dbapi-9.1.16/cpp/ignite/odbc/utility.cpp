/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/odbc/utility.h"
#include "ignite/odbc/system/odbc_constants.h"

#include <algorithm>
#include <cstring>

namespace ignite {

size_t copy_string_to_buffer(const std::string &str, char *buf, std::size_t buffer_len) {
    if (!buf || !buffer_len)
        return 0;

    size_t bytes_to_copy = std::min(str.size(), static_cast<size_t>(buffer_len - 1));

    memcpy(buf, str.data(), bytes_to_copy);
    buf[bytes_to_copy] = 0;

    return bytes_to_copy;
}

std::string sql_string_to_string(const unsigned char *sql_str, std::int32_t sql_str_len) {
    std::string res;

    const char *sql_str_c = reinterpret_cast<const char *>(sql_str);

    if (!sql_str || !sql_str_len)
        return res;

    if (sql_str_len == SQL_NTS)
        res.assign(sql_str_c);
    else if (sql_str_len > 0)
        res.assign(sql_str_c, sql_str_len);

    while (!res.empty() && res.back() == 0)
        res.pop_back();

    return res;
}

} // namespace ignite
