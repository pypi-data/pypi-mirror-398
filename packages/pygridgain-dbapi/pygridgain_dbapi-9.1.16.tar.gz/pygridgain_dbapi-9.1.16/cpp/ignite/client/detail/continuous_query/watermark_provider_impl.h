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
#include "ignite/client/detail/continuous_query/table_row_update_info.h"
#include "ignite/client/table/table_row_event.h"
#include "ignite/common/ignite_error.h"
#include "ignite/common/uuid.h"

#include <atomic>
#include <cstdint>
#include <optional>
#include <set>
#include <vector>

namespace ignite::detail {

/**
 * Continuous Query Watermark Implementation.
 */
class continuous_query_watermark_impl {
public:
    /**
     * Constructor.
     *
     * @param row_ids Row IDs.
     * @param timestamps Timestamps.
     */
    continuous_query_watermark_impl(std::vector<uuid> &&row_ids, std::vector<std::int64_t> &&timestamps)
        : m_row_ids(std::move(row_ids))
        , m_timestamps(std::move(timestamps)) {}

    /**
     * Get row IDs.
     *
     * @return Row IDs.
     */
    [[nodiscard]] const std::vector<uuid> &get_row_ids() const { return m_row_ids; }

    /**
     * Get timestamps.
     *
     * @return Timestamps.
     */
    [[nodiscard]] const std::vector<std::int64_t> &get_timestamps() const { return m_timestamps; }

private:
    /** Per-partition row IDs at the time of this event. */
    std::vector<uuid> m_row_ids;

    /** Per-partition timestamps at the time of this event. */
    std::vector<std::int64_t> m_timestamps;
};

/**
 * Watermark provider class.
 */
class watermark_provider_impl : public watermark_provider {
public:
    /**
     * Constructor.
     *
     * @param part_id Partition ID.
     * @param row_ids Row IDs.
     * @param timestamps Timestamps.
     * @param row_update_infos Rows info.
     */
    watermark_provider_impl(std::int32_t part_id, const std::vector<uuid> &row_ids,
        const std::vector<std::int64_t> &timestamps, const std::vector<table_row_update_info> &row_update_infos)
        : m_part_id(part_id)
        , m_row_ids(row_ids)
        , m_timestamps(timestamps)
        , m_row_update_infos(&row_update_infos) {}


    /**
     * Constructor. Used for creating watermark provider with empty event batch.
     *
     * @param row_ids Row IDs.
     * @param timestamps Timestamps.
     */
    watermark_provider_impl(const std::vector<uuid> &row_ids, const std::vector<std::int64_t> &timestamps)
        : m_part_id(-1)
        , m_row_ids(row_ids)
        , m_timestamps(timestamps)
        , m_row_update_infos(nullptr) {}

    /**
     * Gets the event watermark.
     *
     * @return Event watermark.
     */
    [[nodiscard]] continuous_query_watermark get_watermark(std::int32_t row_batch_idx) const override {
        if (!m_accessible.load()) {
            throw ignite_error("Watermark is not accessible after the call of continuous_query::get_next for"
                               " performance reasons");
        }

        // Clone CQ state and apply the current row update.
        std::vector<uuid> row_ids = m_row_ids;
        std::vector<std::int64_t> timestamps = m_timestamps;

        // The batch is per partition, so we only need to update the corresponding row in the CQ state,
        // This batch does not affect other partitions.
        if (m_part_id >= 0) {
            const table_row_update_info &row_update_info = m_row_update_infos->at(row_batch_idx);
            row_ids[m_part_id] = row_update_info.get_row_id();
            timestamps[m_part_id] = row_update_info.get_timestamp().get_value();
        }

        return continuous_query_watermark{
            std::make_shared<continuous_query_watermark_impl>(std::move(row_ids), std::move(timestamps))};
    }

    /**
     * Mark provider as inaccessible.
     */
    void mark_inaccessible() { m_accessible.store(false); }

    /**
     * Ger partition ID.
     *
     * @return Partition ID.
     */
    [[nodiscard]] std::int32_t get_partition_id() const { return m_part_id; }

private:
    /** Accessibility flag. */
    std::atomic_bool m_accessible{true};

    /** Partition ID. */
    const std::int32_t m_part_id;

    /** Per-partition row IDs at the time of this event. */
    const std::vector<uuid> &m_row_ids;

    /** Per-partition timestamps at the time of this event. */
    const std::vector<std::int64_t> &m_timestamps;

    /** Rows info. */
    const std::vector<table_row_update_info> * m_row_update_infos;
};

} // namespace ignite::detail
