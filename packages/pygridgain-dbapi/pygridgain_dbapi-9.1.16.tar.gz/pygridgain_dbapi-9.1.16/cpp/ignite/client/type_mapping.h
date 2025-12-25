/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/client/table/ignite_tuple.h>

namespace ignite {

/**
 * Function that specifies how a value of a type should be converted to @c ignite_tuple.
 *
 * @tparam T Type of the value.
 * @param value Value to convert.
 * @return An instance of @c ignite_tuple.
 */
template<typename T>
ignite_tuple convert_to_tuple(T &&value);

/**
 * Function that specifies how an @c ignite_tuple instance should be converted to specific type.
 *
 * @tparam T Type to convert to.
 * @param value Instance of the @c ignite_tuple type.
 * @return A resulting value.
 */
template<typename T>
T convert_from_tuple(ignite_tuple &&value);

/**
 * Specialisation for const-references.
 *
 * @tparam T Type to convert from.
 * @param value Value.
 * @return Tuple.
 */
template<typename T>
ignite_tuple convert_to_tuple(const T &value) {
    return convert_to_tuple(T(value));
}

/**
 * Specialisation for optionals.
 *
 * @tparam T Type to convert from.
 * @param value Optional value.
 * @return Optional tuple.
 */
template<typename T>
std::optional<ignite_tuple> convert_to_tuple(std::optional<T> &&value) {
    if (!value.has_value())
        return std::nullopt;

    return {convert_to_tuple<T>(*std::move(value))};
}

/**
 * Specialisation for optionals.
 *
 * @tparam T Type to convert to.
 * @param value Optional tuple.
 * @return Optional value.
 */
template<typename T>
std::optional<T> convert_from_tuple(std::optional<ignite_tuple> &&value) {
    if (!value.has_value())
        return std::nullopt;

    return {convert_from_tuple<T>(*std::move(value))};
}

} // namespace ignite
