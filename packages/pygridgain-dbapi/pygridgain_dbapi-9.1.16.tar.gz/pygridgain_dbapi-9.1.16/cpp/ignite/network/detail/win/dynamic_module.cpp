/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "dynamic_module.h"

#include <sstream>
#include <vector>

namespace {

std::wstring string_to_wstring(const std::string& str)
{
    int ws_len = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), static_cast<int>(str.size()), NULL, 0);

    if (!ws_len)
        return {};

    std::vector<WCHAR> converted(ws_len);

    MultiByteToWideChar(CP_UTF8, 0, str.c_str(), static_cast<int>(str.size()), &converted[0], ws_len);

    std::wstring res(converted.begin(), converted.end());

    return res;
}

} // anonymous namespace

namespace ignite::network {

void* dynamic_module::find_symbol(const char* name)
{
    return GetProcAddress(m_handle, name);
}

bool dynamic_module::is_loaded() const
{
    return m_handle != nullptr;
}

void dynamic_module::unload()
{
    if (is_loaded())
    {
        FreeLibrary(m_handle);

        m_handle = nullptr;
    }
}

dynamic_module load_module(const char* path)
{
    std::string str_path(path);

    return load_module(str_path);
}

dynamic_module load_module(const std::string& path)
{
#ifdef UNICODE
    std::wstring converted_path = string_to_wstring(path);
#else
    const std::string &converted_path = path;
#endif

    HMODULE handle = LoadLibrary(reinterpret_cast<LPCSTR>(converted_path.c_str()));

    return dynamic_module{handle};
}

dynamic_module get_current()
{
    HMODULE handle = GetModuleHandle(NULL);

    return dynamic_module{handle};
}

} // namespace ignite::network
