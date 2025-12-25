/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/continuous_query/continuous_query_options.h"
#include "ignite/client/detail/hybrid_timestamp.h"
#include "ignite/client/detail/table/table_impl.h"
#include "ignite/client/detail/work_thread.h"
#include "ignite/client/table/ignite_tuple.h"
#include "ignite/common/bytes_view.h"
#include "ignite/common/uuid.h"

#include <cassert>
#include <cstdint>
#include <optional>

namespace ignite::detail {

/**
 * Table row. Represents a single row of data of the table.
 */
class table_row {
public:
    /**
     * Constructor.
     *
     * @param data Row data.
     */
    explicit table_row(bytes_view data)
        : m_data(data) {}

    /**
     * Get data.
     *
     * @return Row data.
     */
    [[nodiscard]] bytes_view get_data() const { return m_data; }

private:
    /** Row data. */
    const std::vector<std::byte> m_data;
};

/**
 * Row update info. Represents changes in the table row data.
 */
class table_row_update_info {
public:
    /**
     * Constructor.
     *
     * @param schema_ver Version of table schema.
     * @param row_id Row ID.
     * @param timestamp Timestamp.
     * @param row Row.
     * @param old_row Old row.
     */
    table_row_update_info(
        std::int32_t schema_ver,
        uuid row_id,
        hybrid_timestamp timestamp,
        std::optional<table_row> &&row,
        std::optional<table_row> &&old_row,
        table_row_event_type event_type)
        : m_schema_ver(schema_ver)
        , m_row_id(row_id)
        , m_timestamp(timestamp)
        , m_row(std::move(row))
        , m_old_row(std::move(old_row))
        , m_type(event_type) {
        assert(row.has_value() || old_row.has_value());
    }

    /**
     * Get table schema version.
     *
     * @return Schema version.
     */
    [[nodiscard]] std::int32_t get_schema_ver() const { return m_schema_ver; }

    /**
     * Gets ID of the corresponding row.
     *
     * @return ID of the corresponding row.
     */
    [[nodiscard]] uuid get_row_id() const { return m_row_id; }

    /**
     * Gets commit timestamp of this version.
     *
     * @return Commit timestamp of this version.
     */
    [[nodiscard]] hybrid_timestamp get_timestamp() const { return m_timestamp; }

    /**
     * Returns row data after this update.
     *
     * @return Row data after update.
     */
    [[nodiscard]] std::optional<table_row> &&move_row() { return std::move(m_row); }

    /**
     * Returns row data before this update.
     *
     * @return Row data before update.
     */
    [[nodiscard]] std::optional<table_row> &&move_old_row() { return std::move(m_old_row); }

    /**
     * Returns row data after this update.
     *
     * @return Row data after update.
     */
    [[nodiscard]] const std::optional<table_row> &get_row() const { return m_row; }

    /**
     * Returns row data before this update.
     *
     * @return Row data before update.
     */
    [[nodiscard]] const std::optional<table_row> &get_old_row() const { return m_old_row; }

    /**
     * Return row event type.
     *
     * @return Row event type.
     */
    [[nodiscard]] table_row_event_type get_event_type() const { return m_type; }

private:
    /** Schema version. */
    const std::int32_t m_schema_ver;

    /** Row ID. */
    const uuid m_row_id;

    /** Timestamp. */
    const hybrid_timestamp m_timestamp;

    /** Current row. */
    std::optional<table_row> m_row;

    /** Old row. */
    std::optional<table_row> m_old_row;

    /** Event type. */
    table_row_event_type m_type;
};

} // namespace ignite::detail
