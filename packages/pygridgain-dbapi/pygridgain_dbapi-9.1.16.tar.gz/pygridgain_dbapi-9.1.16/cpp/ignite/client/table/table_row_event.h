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
#include "ignite/common/detail/config.h"

#include <cstdint>
#include <memory>
#include <optional>
#include <set>

namespace ignite {

/**
 * Table row event type.
 */
enum class table_row_event_type : int8_t {
    /// Row created.
    CREATED = 0,

    /// Row updated.
    UPDATED = 1,

    /// Row removed.
    REMOVED = 2,

    /// Row archived into secondary storage.
    ARCHIVED = 3
};

/**
 * Gets all available event types.
 *
 * @return A set containing all table row event types.
 */
inline std::set<table_row_event_type> table_row_event_type_get_all() {
    return {
        table_row_event_type::CREATED,
        table_row_event_type::REMOVED,
        table_row_event_type::UPDATED,
        table_row_event_type::ARCHIVED
    };
}

namespace detail {

/**
 * Watermark provider class.
 */
class watermark_provider {
public:
    /**
     * Gets the event watermark.
     *
     * @return Event watermark.
     */
    [[nodiscard]] virtual continuous_query_watermark get_watermark(std::int32_t row_batch_idx) const = 0;

protected:
    // Default
    watermark_provider() = default;
};

} // namespace detail

/**
 * @brief Table row event.
 * Produced by continuous query.
 * @tparam T Table row type.
 */
template<typename T>
class table_row_event {
public:
    /** Value type. */
    typedef T value_type;

    // Default
    table_row_event() = default;

    /**
     * Constructor.
     *
     * @param row_idx Row index.
     * @param entry Entry.
     * @param old_entry Old entry.
     * @param event_type Event type.
     * @param watermark_provider Watermark provider.
     */
    table_row_event(
        std::int32_t row_idx,
        std::optional<value_type> &&entry,
        std::optional<value_type> &&old_entry,
        table_row_event_type event_type,
        std::shared_ptr<detail::watermark_provider> watermark_provider)
        : m_row_idx(row_idx)
        , m_entry(std::move(entry))
        , m_old_entry(std::move(old_entry))
        , m_type(event_type)
        , m_watermark_provider(std::move(watermark_provider)) {
    }

    /**
     * Gets the event type.
     *
     * @return Event type.
     */
    [[nodiscard]] table_row_event_type get_type() const { return m_type; }

    /**
     * Gets the resulting entry value.
     * @c std::nullopt if the event type is @c table_row_event_type::REMOVED.
     *
     * @return Resulting entry value.
     */
    [[nodiscard]] const std::optional<value_type> &get_entry() const { return m_entry; }

    /**
     * Gets the previous entry value.
     * @c std::nullopt if the event type is @c table_row_event_type::CREATED.
     *
     * @return Previous entry value.
     */
    [[nodiscard]] const std::optional<value_type> &get_old_entry() const { return m_old_entry; }

    /**
     * Gets the event watermark for resume and failover purposes. Pass the value to
     * @c continuous_query_options::set_watermark() in order to resume the query from the current event (exclusive).
     * This provides uninterrupted stream of events with exactly-once semantics in case of application restarts,
     * failover on another node, etc.
     *
     * @note For performance reasons, this property can't be accessed after the next @c continuous_query::get_next or
     *      @c continuous_query::get_next_async methods are called.
     *
     * @return Event watermark.
     */
    [[nodiscard]] continuous_query_watermark get_watermark() const {
        return m_watermark_provider->get_watermark(m_row_idx);
    }

private:
    /** Row ID. */
    std::int32_t m_row_idx{-1};

    /** Entry. */
    std::optional<value_type> m_entry{};

    /** Old entry. */
    std::optional<value_type> m_old_entry{};

    /** Event type. */
    table_row_event_type m_type{table_row_event_type::CREATED};

    /** Watermark provider. */
    std::shared_ptr<detail::watermark_provider> m_watermark_provider;
};

} // namespace ignite
