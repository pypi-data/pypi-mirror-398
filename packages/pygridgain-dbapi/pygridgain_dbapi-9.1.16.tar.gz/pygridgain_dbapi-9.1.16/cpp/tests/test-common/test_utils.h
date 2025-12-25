/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/ignite_result.h"

#include <chrono>
#include <functional>
#include <future>
#include <string>
#include <filesystem>
#include <thread>
#include <type_traits>

#include <cstdio>

namespace ignite {

/**
 * Resolve IGNITE_HOME directory. Resolution is performed in several steps:
 * 1) Check for path provided as argument.
 * 2) Check for environment variable.
 * 3) Check for current working directory.
 * Result of these checks are evaluated based on existence of certain predefined folders inside possible Ignite
 * home. If they are found, IGNITE_HOME is considered resolved.
 *
 * @param path Optional path to check.
 * @return Resolved Ignite home.
 */
std::string resolve_ignite_home(const std::string &path = "");


/**
 * Resolve test directory. Relies on Ignite Home resolving inside.
 *
 * @return Resolved tests directory path.
 */
std::filesystem::path resolve_test_dir();

/**
 * Generates a path in the temporary directory.
 * @param subDir Optional subdirectory.
 * @param prefix Optional prefix.
 * @return Filesystem path to the generated temporary directory.
 */
std::filesystem::path resolve_temp_dir(std::string_view subDir = "", std::string_view prefix = "");

/**
 * Check async operation result and propagate error to the promise if there is
 * any.
 *
 * @tparam T Result type.
 * @param prom Promise to set.
 * @param res Result to check.
 * @return @c true if there is no error and @c false otherwise.
 */
template<typename T1, typename T2>
bool check_and_set_operation_error(std::promise<T2> &prom, const ignite_result<T1> &res) {
    if (res.has_error()) {
        prom.set_exception(std::make_exception_ptr(res.error()));
        return false;
    }
    return true;
}

/**
 * Check whether test cluster is connectable.
 *
 * @param timeout Timeout.
 * @return @c true if cluster is connectable.
 */
bool check_test_node_connectable(std::chrono::seconds timeout);

/**
 * Make sure that test cluster is connectable.
 * Throws on fail.
 *
 * @param timeout Timeout.
 */
void ensure_node_connectable(std::chrono::seconds timeout);

/**
 * Wait for condition.
 *
 * @param timeout Timeout.
 * @param predicate Predicate.
 * @return @c true if condition is turned @c true within timeout, @c false otherwise.
 */
bool wait_for_condition(std::chrono::seconds timeout, const std::function<bool()> &predicate);

/**
 * Wait for the specified conditions.
 *
 * @param timeout Timeout to wait for.
 * @param predicate Predicate to check.
 * @return @c true if the condition was met within timeout.
 */
template<typename T1, typename T2>
bool wait_for_condition(std::chrono::duration<T1, T2> timeout, const std::function<bool()> &predicate) {
    using namespace std::chrono_literals;

    auto end = std::chrono::steady_clock::now() + timeout;
    do {
        if (predicate())
            return true;

        std::this_thread::sleep_for(100ms);
    } while (std::chrono::steady_clock::now() < end);

    return false;
}

} // namespace ignite
