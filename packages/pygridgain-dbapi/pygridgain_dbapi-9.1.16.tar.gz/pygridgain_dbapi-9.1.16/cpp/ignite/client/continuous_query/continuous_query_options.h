/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/continuous_query/continuous_query_watermark.h"
#include "ignite/client/table/table_row_event.h"

#include <cstdint>
#include <set>
#include <string>

namespace ignite {

/**
 * @brief Continuous query options.
 */
class continuous_query_options {
public:
    // Default
    continuous_query_options() = default;

    /**
     * Gets the per-partition page size.
     *
     * Continuous Query polls every partition in a loop. This parameter controls the number of entries that will be
     * requested from a single partition in one network call. Therefore, the maximum number of entries that the query
     * may hold in memory at any given time is <tt>get_page_size() * get_partitions()</tt>.
     *
     * @return Page size.
     */
    [[nodiscard]] std::int32_t get_page_size() const { return m_page_size; }

    /**
     * Sets the per-partition page size.
     *
     * @see See get_page_size() for details.
     * @param page_size Page size.
     */
    continuous_query_options& set_page_size(std::int32_t page_size) {
        m_page_size = page_size;
        return *this;
    }

    /**
     * Gets the poll interval in milliseconds.
     *
     * @return Poll interval in milliseconds.
     */
    [[nodiscard]] std::int32_t get_poll_interval_ms() const { return m_poll_interval_ms; }

    /**
     * Sets the poll interval in milliseconds.
     *
     * @param poll_interval_ms Poll interval in milliseconds.
     */
    continuous_query_options& set_poll_interval_ms(std::int32_t poll_interval_ms) {
        m_poll_interval_ms = poll_interval_ms;
        return *this;
    }

    /**
     * Gets the included event types.
     *
     * @return Included event types.
     */
    [[nodiscard]] const std::set<table_row_event_type> &get_event_types() const { return m_event_types; }

    /**
     * Sets the included event types.
     *
     * @see Also, you can use table_row_event_type_get_all() to get set of all available event types.
     * @param event_types Included event types.
     */
    continuous_query_options& set_event_types(const std::set<table_row_event_type> &event_types) {
        m_event_types = event_types;
        return *this;
    }

    /**
     * Gets the included column names.
     *
     * @return Names of the included columns. If empty, all columns are included.
     */
    [[nodiscard]] const std::set<std::string> &get_column_names() const { return m_column_names; }

    /**
     * Sets the included column names.
     *
     * @param column_names Names of the included columns. If empty, all columns are included.
     */
    continuous_query_options& set_column_names(const std::set<std::string> &column_names) {
        m_column_names = column_names;
        return *this;
    }

    /**
     * Gets the starting watermark. When @c std::nullopt, the query will start from the current time.
     *
     * Watermark can be obtained with @c continuous_query_watermark::of_timestamp(), or from an event with
     * @c table_row_event::get_watermark(). The latter allows resuming a query from a specific event (excluding said
     * event, providing exactly-once semantics).
     *
     * @return Watermark to start from.
     */
    [[nodiscard]] const std::optional<continuous_query_watermark> &get_watermark() const { return m_watermark; }

    /**
     * Sets the starting watermark. When @c std::nullopt, the query will start from the current time.
     *
     * @see See get_watermark() for details.
     * @param watermark Watermark to start from.
     */
    continuous_query_options& set_watermark(const std::optional<continuous_query_watermark> &watermark) {
        m_watermark = watermark;
        return *this;
    }

    [[nodiscard]] bool get_enable_empty_batches() const { return m_enable_empty_batches; }

    /**
     * Allows CQ to produce empty batches when no events were received.
     * It may be useful if table updates are rare and user need to update actual watermarks.
     * Otherwise, when restarting CQ user might provide watermark which is too old.
     *
     * @param enable_empty_batches True if empty batches enabled, false otherwise.
     */
    continuous_query_options& set_enable_empty_batches(bool enable_empty_batches) {
        m_enable_empty_batches = enable_empty_batches;
        return *this;
    }

private:
    /** Per-partition page size. */
    std::int32_t m_page_size{1000};

    /** Poll interval in milliseconds. */
    std::int32_t m_poll_interval_ms{1000};

    /** Included event types. */
    std::set<table_row_event_type> m_event_types{table_row_event_type_get_all()};

    /** Names of the included columns. */
    std::set<std::string> m_column_names{};

    /** Watermark to start from. */
    std::optional<continuous_query_watermark> m_watermark{std::nullopt};

    /** Allows continuous query to receive empty batches.*/
    bool m_enable_empty_batches{false};
};

} // namespace ignite
