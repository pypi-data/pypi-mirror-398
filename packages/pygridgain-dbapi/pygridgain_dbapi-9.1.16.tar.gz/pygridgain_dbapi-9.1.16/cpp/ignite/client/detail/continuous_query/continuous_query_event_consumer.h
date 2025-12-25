/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/client/detail/table/packed_tuple.h>
#include <ignite/client/table/ignite_tuple.h>
#include <ignite/client/table/table_row_event.h>
#include <ignite/client/table/table_row_event_batch.h>
#include <ignite/client/type_mapping.h>
#include <ignite/common/ignite_result.h>

#include <atomic>
#include <cstdint>
#include <optional>

namespace ignite::detail {

/**
 * Event Consumer.
 */
class continuous_query_event_consumer {
public:
    // Default
    virtual ~continuous_query_event_consumer() = default;

    /**
     * Handle new entry.
     *
     * @param row_idx Row index.
     * @param entry Entry.
     * @param old_entry Old entry.
     * @param event_type Row event type.
     * @param watermark_provider Watermark provider.
     */
    virtual void handle_entry(
        std::int32_t row_idx,
        std::optional<packed_tuple> &&entry,
        std::optional<packed_tuple> &&old_entry,
        table_row_event_type event_type,
        std::shared_ptr<detail::watermark_provider> watermark_provider) = 0;

    /**
     * Flush saved entries to consumer.
     */
    virtual void complete() = 0;

    /**
     * Handle error.
     *
     * @param error Error.
     */
    virtual void complete_with_error(ignite_error &&error) = 0;

    /**
     * Completes consumer with empty batch.
     *
     * @param watermark_provider Watermark provider.
     */
    virtual void complete_empty(std::shared_ptr<detail::watermark_provider> watermark_provider) = 0;
};

/**
 * Basic implementation.
 */
template<typename T>
class continuous_query_event_consumer_basic : public continuous_query_event_consumer {
public:
    /** Value type. */
    typedef T entry_type;

    // Default
    continuous_query_event_consumer_basic() = default;
    ~continuous_query_event_consumer_basic() override = default;

    /**
     * Constructor.
     *
     * @param callback Callback.
     */
    explicit continuous_query_event_consumer_basic(ignite_callback<table_row_event_batch<entry_type>> callback)
        : m_callback(std::move(callback)) {}

    void complete() override {
        auto was_complete = m_complete.exchange(true);
        if (!was_complete) {
            m_callback(table_row_event_batch<entry_type>{std::move(m_batch)});
        }
    }

    void complete_with_error(ignite_error &&error) override {
        auto was_complete = m_complete.exchange(true);
        if (!was_complete) {
            m_callback(std::move(error));
        }
    }

    void complete_empty(std::shared_ptr<detail::watermark_provider> watermark_provider) override {
        auto was_complete = m_complete.exchange(true);
        if (!was_complete) {
            m_callback(table_row_event_batch<entry_type>{watermark_provider});
        }
    }

protected:
    /** Completion flag. */
    std::atomic_bool m_complete = false;

    /** Batch. */
    std::vector<table_row_event<entry_type>> m_batch;

    /** Callback. */
    const ignite_callback<table_row_event_batch<entry_type>> m_callback;
};

/**
 * Events consumer implementation for records.
 */
template<typename T>
class continuous_query_event_consumer_record : public continuous_query_event_consumer_basic<T> {
public:
    /** Value type. */
    typedef T entry_type;

    // Default
    continuous_query_event_consumer_record() = default;
    ~continuous_query_event_consumer_record() override = default;

    /**
     * Constructor.
     *
     * @param callback Callback.
     */
    explicit continuous_query_event_consumer_record(ignite_callback<table_row_event_batch<entry_type>> callback)
        : continuous_query_event_consumer_basic<T>(std::move(callback)) {}

    void handle_entry(
        std::int32_t row_idx,
        std::optional<packed_tuple> &&entry,
        std::optional<packed_tuple> &&old_entry,
        table_row_event_type event_type,
        std::shared_ptr<detail::watermark_provider> watermark_provider) override {
        std::optional<ignite_tuple> tuple_entry;
        if (entry)
            tuple_entry = entry->unpack(false);

        std::optional<ignite_tuple> tuple_old_entry;
        if (old_entry)
            tuple_old_entry = old_entry->unpack(false);

        if constexpr (std::is_same<entry_type, ignite_tuple>::value) {
            this->m_batch.emplace_back(
                row_idx, std::move(tuple_entry), std::move(tuple_old_entry), event_type, std::move(watermark_provider));
        } else {
            auto record = convert_from_tuple<entry_type>(std::move(tuple_entry));
            auto old_record = convert_from_tuple<entry_type>(std::move(tuple_old_entry));

            this->m_batch.emplace_back(
                row_idx, std::move(record), std::move(old_record), event_type, std::move(watermark_provider));
        }
    }
};

/**
 * Events consumer implementation for key-value pairs.
 */
template<typename K, typename V>
class continuous_query_event_consumer_kv : public continuous_query_event_consumer_basic<std::pair<K, V>> {
public:
    /** Key type. */
    typedef K key_type;

    /** Value type. */
    typedef V value_type;

    /** Entry type. */
    typedef std::pair<key_type, value_type> entry_type;

    // Default
    continuous_query_event_consumer_kv() = default;
    ~continuous_query_event_consumer_kv() override = default;

    /**
     * Constructor.
     *
     * @param callback Callback.
     */
    explicit continuous_query_event_consumer_kv(ignite_callback<table_row_event_batch<entry_type>> callback)
        : continuous_query_event_consumer_basic<entry_type>(std::move(callback)) {}

    void handle_entry(
        std::int32_t row_idx,
        std::optional<packed_tuple> &&entry,
        std::optional<packed_tuple> &&old_entry,
        table_row_event_type event_type,
        std::shared_ptr<detail::watermark_provider> watermark_provider) override {
        std::optional<std::pair<ignite_tuple, ignite_tuple>> pair;
        if (entry)
            pair = std::make_pair(entry->unpack_key(), entry->unpack_value());

        std::optional<std::pair<ignite_tuple, ignite_tuple>> pair_old;
        if (old_entry)
            pair_old = std::make_pair(old_entry->unpack_key(), old_entry->unpack_value());

        if constexpr (std::is_same<entry_type, std::pair<ignite_tuple, ignite_tuple>>::value) {
            this->m_batch.emplace_back(row_idx, std::move(pair), std::move(pair_old), event_type, std::move(watermark_provider));
        } else {
            std::optional<entry_type> pair_unpacked;
            if (pair) {
                pair_unpacked = std::make_pair(convert_from_tuple<key_type>(std::move(pair->first)),
                    convert_from_tuple<value_type>(std::move(pair->second)));
            }

            std::optional<entry_type> pair_old_unpacked;
            if (pair_old) {
                pair_old_unpacked = std::make_pair(convert_from_tuple<key_type>(std::move(pair_old->first)),
                    convert_from_tuple<value_type>(std::move(pair_old->second)));
            }

            this->m_batch.emplace_back(
                row_idx, std::move(pair_unpacked), std::move(pair_old_unpacked), event_type, std::move(watermark_provider));
        }
    }
};

} // namespace ignite::detail
