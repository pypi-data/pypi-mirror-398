/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/table/table_row_event.h"

#include <vector>

namespace ignite {

/**
 * @brief Batch of @ref table_row_event.
 *
 * @tparam T Table row type.
 */
template<typename T>
class table_row_event_batch {
public:
    /** Value type. */
    typedef T value_type;

    // Default
    table_row_event_batch() = default;

    /**
     * Internal API.
     * Constructor.
     *
     * @param events Vector of events. Should not be empty.
     */
    explicit table_row_event_batch(std::vector<table_row_event<value_type>> &&events)
        : m_events(std::move(events)) {}

    /**
     * Internal API.
     * Constructor.
     *
     * @param watermark_provider Watermark provider.
     */
    explicit table_row_event_batch(std::shared_ptr<detail::watermark_provider> watermark_provider)
        : m_watermark_provider(std::move(watermark_provider)) {}


    /**
     * Gets the events.
     *
     * @return Events.
     */
    [[nodiscard]] const std::vector<table_row_event<value_type>> &get_events() const & { return m_events; }

    /**
     * Gets the events.
     *
     * @return Events.
     */
    [[nodiscard]] std::vector<table_row_event<value_type>> &&get_events() && { return std::move(m_events); }

    /**
     * Gets the watermark for the batch.
     *
     * @return Watermark for the batch.
     */
    [[nodiscard]] continuous_query_watermark get_watermark() const {
        if (m_events.empty()) {
            return m_watermark_provider->get_watermark(-1);
        }

        return m_events.rbegin()->get_watermark();
    }

private:
    /** Table row events. */
    std::vector<table_row_event<value_type>> m_events{};

    /** Watermark provider. Required when batch contains no events. */
    std::shared_ptr<detail::watermark_provider> m_watermark_provider{};
};

} // namespace ignite
