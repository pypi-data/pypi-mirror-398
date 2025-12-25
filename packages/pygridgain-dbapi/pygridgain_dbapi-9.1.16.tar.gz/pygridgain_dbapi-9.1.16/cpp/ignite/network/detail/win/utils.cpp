/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "../utils.h"

#include <windows.h>

// Using NULLs as specified by WinAPI
#ifdef __JETBRAINS_IDE__
# pragma ide diagnostic ignored "modernize-use-nullptr"
#endif

namespace ignite::network::detail {

std::string get_last_system_error() {
    DWORD error_code = GetLastError();

    std::string error_details;
    if (error_code != ERROR_SUCCESS) {
        char errBuf[1024] = {};

        FormatMessageA(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL, error_code,
            MAKELANGID(LANG_ENGLISH, SUBLANG_ENGLISH_US), errBuf, sizeof(errBuf), NULL);

        error_details.assign(errBuf);
    }

    return error_details;
}

} // namespace ignite::network::detail
