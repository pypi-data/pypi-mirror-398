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

#include <ignite/common/bytes_view.h>
#include <ignite/common/detail/config.h>

#include <memory>

namespace ignite::detail {
// Forward declaration.
struct schema;

/**
 * Packed tuple.
 */
class packed_tuple {
public:
    /**
     * Constructor.
     *
     * @param data Data.
     */
    packed_tuple(bytes_view data, std::shared_ptr<schema> sch)
        : m_data(data)
        , m_schema(std::move(sch)) {}

    /**
     * Unpack the full tuple.
     *
     * @param key_only Indicate if the only key part of the tuple is available.
     * @return Tuple.
     */
    [[nodiscard]] IGNITE_API ignite_tuple unpack(bool key_only) const;

    /**
     * Unpack the key part of the tuple.
     *
     * @return Tuple.
     */
    [[nodiscard]] IGNITE_API ignite_tuple unpack_key() const;

    /**
     * Unpack the value part of the tuple.
     *
     * @return Tuple.
     */
    [[nodiscard]] IGNITE_API ignite_tuple unpack_value() const;

private:
    /** Data. */
    bytes_view m_data;

    /** Schema. */
    std::shared_ptr<schema> m_schema;
};

} // namespace ignite::detail
