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

#include <dlfcn.h>

namespace ignite::network
{

void* dynamic_module::find_symbol(const char* name)
{
    return dlsym(m_handle, name);
}

bool dynamic_module::is_loaded() const
{
    return m_handle != nullptr;
}

void dynamic_module::unload()
{
    if (is_loaded())
        dlclose(m_handle);
}

dynamic_module load_module(const char* path)
{
    void* handle = dlopen(path, RTLD_NOW);

    return dynamic_module(handle);
}

dynamic_module load_module(const std::string& path)
{
    return load_module(path.c_str());
}

dynamic_module get_current()
{
    return load_module(NULL);
}

}
