/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/detail/continuous_query/continuous_query_event_consumer.h"
#include "ignite/client/table/ignite_tuple.h"
#include "ignite/client/table/table_row_event_batch.h"

#include "ignite/common/detail/config.h"
#include "ignite/common/ignite_result.h"

#include <memory>

namespace ignite {

namespace detail {
// Forward declaration
class continuous_query_impl;
}

/**
 * @brief Continuous query template.
 */
template<typename T>
class continuous_query;

/**
 * @brief Continuous query specialisations for the @c ignite_tuple.
 */
template<>
class continuous_query<ignite_tuple> {
    template<typename T>
    friend class continuous_query;

public:
    /** Value type. */
    typedef ignite_tuple entry_type;

    // Default
    continuous_query() = default;

    /**
     * Constructor.
     *
     * Internal method.
     *
     * @param impl Implementation.
     */
    explicit continuous_query(std::shared_ptr<detail::continuous_query_impl> impl)
        : m_impl(std::move(impl)) {}

    /**
     * Gets the next batch of events asynchronously.
     *
     * @warning Continues query is not thread-safe, so this method should not be called concurrently. If you need to
     *  call this method from different threads, make sure to add additional synchronisation (e.g. mutex).
     *
     * @param callback Callback to be called with the result of the operation.
     */
    IGNITE_API void get_next_async(ignite_callback<table_row_event_batch<entry_type>> callback);

    /**
     * Gets the next batch of events.
     *
     * @warning Continues query is not thread-safe, so this method should not be called concurrently. If you need to
     *  call this method from different threads, make sure to add additional synchronisation (e.g. mutex).
     *
     * @return The next batch of events.
     */
    [[nodiscard]] IGNITE_API table_row_event_batch<entry_type> get_next() {
        return sync<table_row_event_batch<entry_type>>([this](auto callback) { get_next_async(std::move(callback)); });
    }

    /**
     * Check the query for completion.
     *
     * @return @c true if complete.
     */
    [[nodiscard]] IGNITE_API bool is_complete() const;

    /**
     * Cancel the query.
     */
    void IGNITE_API cancel();

private:
    /**
     * Get next batch of events.
     *
     * @param consumer Events consumer.
     */
    IGNITE_API void get_next_async(std::shared_ptr<detail::continuous_query_event_consumer> consumer);

    /** Implementation. */
    std::shared_ptr<detail::continuous_query_impl> m_impl;
};

/**
 * @brief Continuous query template for records.
 */
template<typename T>
class continuous_query {
public:
    /** Value type. */
    typedef T entry_type;

    // Default
    continuous_query() = default;

    /**
     * Constructor.
     *
     * Internal method.
     *
     * @param delegate Delegate.
     */
    explicit continuous_query(continuous_query<ignite_tuple> delegate)
        : m_delegate(std::move(delegate)) {}

    /**
     * Gets the next batch of events asynchronously.
     *
     * @warning Continues query is not thread-safe, so this method should not be called concurrently. If you need to
     *  call this method from different threads, make sure to add additional synchronisation (e.g. mutex).
     *
     * @param callback Callback to be called with the result of the operation.
     */
    void get_next_async(ignite_callback<table_row_event_batch<entry_type>> callback) {
        typedef detail::continuous_query_event_consumer_record<entry_type> consumer_type;
        m_delegate.get_next_async(std::make_shared<consumer_type>(std::move(callback)));
    }

    /**
     * Gets the next batch of events.
     *
     * @warning Continues query is not thread-safe, so this method should not be called concurrently. If you need to
     *  call this method from different threads, make sure to add additional synchronisation (e.g. mutex).
     *
     * @return The next batch of events.
     */
    [[nodiscard]] table_row_event_batch<entry_type> get_next() {
        return sync<table_row_event_batch<entry_type>>([this](auto callback) { get_next_async(std::move(callback)); });
    }

    /**
     * Check the query for completion.
     *
     * @return @c true if complete.
     */
    [[nodiscard]] bool is_complete() const { return m_delegate.is_complete(); }

    /**
     * Cancel the query.
     */
    void cancel() { m_delegate.cancel(); }

private:
    /** Delegate. */
    continuous_query<ignite_tuple> m_delegate;
};

/**
 * @brief Continuous query specialisations for binary key-value view.
 */
template<>
class continuous_query<std::pair<ignite_tuple, ignite_tuple>> {
    template<typename T>
    friend class continuous_query;

public:
    /** Key type. */
    typedef ignite_tuple key_type;

    /** Value type. */
    typedef ignite_tuple value_type;

    /** Entry type. */
    typedef std::pair<key_type, value_type> entry_type;

    // Default
    continuous_query() = default;

    /**
     * Constructor.
     *
     * Internal method.
     *
     * @param impl Implementation.
     */
    explicit continuous_query(std::shared_ptr<detail::continuous_query_impl> impl)
        : m_impl(std::move(impl)) {}

    /**
     * Gets the next batch of events asynchronously.
     *
     * @warning Continues query is not thread-safe, so this method should not be called concurrently. If you need to
     *  call this method from different threads, make sure to add additional synchronisation (e.g. mutex).
     *
     * @param callback Callback to be called with the result of the operation.
     */
    IGNITE_API void get_next_async(ignite_callback<table_row_event_batch<entry_type>> callback);

    /**
     * Gets the next batch of events.
     *
     * @warning Continues query is not thread-safe, so this method should not be called concurrently. If you need to
     *  call this method from different threads, make sure to add additional synchronisation (e.g. mutex).
     *
     * @return The next batch of events.
     */
    [[nodiscard]] IGNITE_API table_row_event_batch<entry_type> get_next() {
        return sync<table_row_event_batch<entry_type>>([this](auto callback) { get_next_async(std::move(callback)); });
    }

    /**
     * Check the query for completion.
     *
     * @return @c true if complete.
     */
    [[nodiscard]] IGNITE_API bool is_complete() const;

    /**
     * Cancel the query.
     */
    void IGNITE_API cancel();

private:
    /**
     * Get next batch of events.
     *
     * @param consumer Events consumer.
     */
    IGNITE_API void get_next_async(std::shared_ptr<detail::continuous_query_event_consumer> consumer);

    /** Implementation. */
    std::shared_ptr<detail::continuous_query_impl> m_impl;
};

/**
 * @brief Continuous query template for key-value.
 */
template<typename K, typename V>
class continuous_query<std::pair<K, V>> {
public:
    /** Key type. */
    typedef K key_type;

    /** Value type. */
    typedef V value_type;

    /** Entry type. */
    typedef std::pair<key_type, value_type> entry_type;

    // Default
    continuous_query() = default;

    /**
     * Constructor.
     *
     * Internal method.
     *
     * @param delegate Delegate.
     */
    explicit continuous_query(continuous_query<std::pair<ignite_tuple, ignite_tuple>> delegate)
        : m_delegate(std::move(delegate)) {}

    /**
     * Gets the next batch of events asynchronously.
     *
     * @warning Continues query is not thread-safe, so this method should not be called concurrently. If you need to
     *  call this method from different threads, make sure to add additional synchronisation (e.g. mutex).
     *
     * @param callback Callback to be called with the result of the operation.
     */
    void get_next_async(ignite_callback<table_row_event_batch<entry_type>> callback) {
        typedef detail::continuous_query_event_consumer_kv<key_type, value_type> consumer_type;
        m_delegate.get_next_async(std::make_shared<consumer_type>(std::move(callback)));
    }

    /**
     * Gets the next batch of events.
     *
     * @warning Continues query is not thread-safe, so this method should not be called concurrently. If you need to
     *  call this method from different threads, make sure to add additional synchronisation (e.g. mutex).
     *
     * @return The next batch of events.
     */
    [[nodiscard]] table_row_event_batch<entry_type> get_next() {
        return sync<table_row_event_batch<entry_type>>([this](auto callback) { get_next_async(std::move(callback)); });
    }

    /**
     * Check the query for completion.
     *
     * @return @c true if complete.
     */
    [[nodiscard]] bool is_complete() const { return m_delegate.is_complete(); }

    /**
     * Cancel the query.
     */
    void cancel() { m_delegate.cancel(); }

private:
    /** Delegate. */
    continuous_query<std::pair<ignite_tuple, ignite_tuple>> m_delegate;
};

} // namespace ignite
