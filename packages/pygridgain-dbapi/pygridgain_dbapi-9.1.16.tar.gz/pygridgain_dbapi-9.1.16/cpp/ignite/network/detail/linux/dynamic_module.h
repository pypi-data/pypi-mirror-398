/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <string>

namespace ignite::network
{

/**
 * Represents dynamically loadable program module such as dynamic or shared library.
 */
class dynamic_module
{
public:
    /**
     * Default constructor.
     */
    dynamic_module() = default;

    /**
     * Handle constructor.
     *
     * @param handle Os-specific module handle.
     */
    dynamic_module(void* handle) : m_handle(handle) {}

    /**
     * Load symbol from module.
     *
     * @param name Name of the symbol to load.
     * @return Pointer to symbol if found and NULL otherwise.
     */
    void* find_symbol(const char* name);

    /**
     * Load symbol from module.
     *
     * @param name Name of the symbol to load.
     * @return Pointer to symbol if found and NULL otherwise.
     */
    void* find_symbol(const std::string& name)
    {
        return find_symbol(name.c_str());
    }

    /**
     * Check if the instance is loaded.
     *
     * @return True if the instance is loaded.
     */
    bool is_loaded() const;

    /**
     * Unload module.
     */
    void unload();

private:
    void* m_handle{nullptr};
};

/**
 * Load module by the specified path.
 *
 * @param path Path to the module to load.
 * @return Module instance.
 */
dynamic_module load_module(const char* path);

/**
 * Load module by the specified path.
 *
 * @param path Path to the module to load.
 * @return Module instance.
 */
dynamic_module load_module(const std::string& path);

/**
 * Returns module associated with the calling process itself.
 *
 * @return Module for the calling process.
 */
dynamic_module get_current();

}
