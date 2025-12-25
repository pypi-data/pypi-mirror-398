/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "../utils.h"

#include <cstring>

namespace ignite::network::detail {

#if defined(__linux__)
std::string get_last_system_error() {
    int error_code = errno;

    std::string error_details;
    if (error_code != 0) {
        char err_buf[1024] = {0};

        const char *res = strerror_r(error_code, err_buf, sizeof(err_buf));
        if (res)
            error_details.assign(res);
    }

    return error_details;
}
#elif defined(__APPLE__)
std::string get_last_system_error() {
    int error_code = errno;

    std::string error_details;
    if (error_code != 0) {
        char err_buf[1024] = {0};

        const int res = strerror_r(error_code, err_buf, sizeof(err_buf));

        switch (res) {
            case 0:
                error_details.assign(err_buf);
                break;
            case ERANGE:
                // Buffer too small.
                break;
            default:
            case EINVAL:
                // Invalid error code.
                break;
        }
    }

    return error_details;
}
#endif

} // namespace ignite::network::detail
