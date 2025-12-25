/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/detail/config.h"
#include "ignite/common/ignite_timestamp.h"

#include <cstdint>
#include <memory>
#include <string>

namespace ignite {

namespace detail {
class continuous_query_impl;
class continuous_query_watermark_impl;
class watermark_provider_impl;
class watermark_accessor;
}

/**
 * @brief Continuous query watermark.
 * Represents a starting point for a continuous query.
 */
class continuous_query_watermark {
    friend class detail::continuous_query_impl;
    friend class detail::watermark_provider_impl;
    friend class detail::watermark_accessor;

public:
    // Default
    continuous_query_watermark() = default;

    /**
     * Creates a new watermark based on specified time (wall clock).
     *
     * The specified timestamp should not be older than server's
     * <tt>now() - LowWatermarkConfiguration.dataAvailabilityTime()</tt>, or the query will fail with an exception.
     *
     * @param start_time Start time.
     * @return Watermark.
     */
    static IGNITE_API continuous_query_watermark of_timestamp(ignite_timestamp start_time) {
        return continuous_query_watermark{start_time};
    }

    /**
     * Convert an object to a string.
     * Uses JSON-format.
     *
     * @return A string.
     */
    [[nodiscard]] IGNITE_API std::string to_string() const;

    /**
     * Convert from string.
     *
     * The string is supposed to be obtained using @see to_string() method.
     * @param str String representation of the object.
     * @return An instance.
     */
    static IGNITE_API continuous_query_watermark from_string(std::string_view str);

private:
    explicit continuous_query_watermark(ignite_timestamp timestamp)
        : m_timestamp((timestamp.get_epoch_second() * 1000) + (timestamp.get_nano() / 1'000'000)) {}

    explicit continuous_query_watermark(std::shared_ptr<detail::continuous_query_watermark_impl> impl)
        : m_impl(std::move(impl)) {}

    /** Timestamp. */
    std::int64_t m_timestamp{0};

    /** Implementation. */
    std::shared_ptr<detail::continuous_query_watermark_impl> m_impl{};
};

} // namespace ignite
