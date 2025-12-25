/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/common/ignite_error.h>

#include <future>
#include <memory>
#include <utility>
#include <optional>
#include <string>

namespace ignite::detail {

/**
 * Make future error.
 *
 * @tparam T Value type.
 * @param err Error.
 * @return Failed future with the specified error.
 */
template<typename T>
std::future<T> make_future_error(ignite_error err) {
    std::promise<T> promise;
    promise.set_exception(std::make_exception_ptr(std::move(err)));

    return promise.get_future();
}

/**
 * Make future value.
 *
 * @tparam T Value type.
 * @param value Value.
 * @return Failed future with the specified error.
 */
template<typename T>
std::future<T> make_future_value(T value) {
    std::promise<T> promise;
    promise.set_value(std::move(value));

    return promise.get_future();
}

/**
 * Get environment variable.
 *
 * @param name Variable name.
 * @return Variable value if it is set, or @c std::nullopt otherwise.
 */
inline std::optional<std::string> get_env(const std::string &name) {
    const char *env = std::getenv(name.c_str());
    if (!env)
        return {};

    return env;
}

} // namespace ignite::detail
