/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/table/ignite_tuple.h"

#include <string>

namespace ignite::detail::arg_check {

/**
 * Check that the condition is true.
 *
 * @param condition Condition to test.
 * @param message Message to use in an exception if the condition is false.
 */
void inline is_true(bool condition, const std::string &message) {
    if (!condition)
        throw ignite_error(error::code::ILLEGAL_ARGUMENT, message);
}

/**
 * Check key argument.
 *
 * @param value Value.
 * @param title Title.
 */
void inline tuple_non_empty(const ignite_tuple &value, const std::string &title) {
    is_true(0 != value.column_count(), title + " can not be empty");
}

/**
 * Check key argument.
 *
 * @param key Key tuple.
 */
void inline key_tuple_non_empty(const ignite_tuple &key) {
    tuple_non_empty(key, "Key tuple");
}

/**
 * Check value argument.
 *
 * @param value Value tuple.
 */
void inline value_tuple_non_empty(const ignite_tuple &value) {
    tuple_non_empty(value, "Value tuple");
}

/**
 * Check container argument.
 *
 * @param cont Value tuple.
 * @param title Title.
 */
template<typename T>
void container_non_empty(const T &cont, const std::string &title) {
    is_true(!cont.empty(), title + " can not be empty");
}

/**
 * Check pointer argument.
 *
 * @param ptr Pointer.
 * @param title Title.
 */
template<typename T>
void pointer_valid(const T &ptr, const std::string &title) {
    is_true(static_cast<bool>(ptr), title + " can not be nullptr");
}

} // namespace ignite::detail::arg_check
