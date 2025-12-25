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
#include "ignite/client/detail/continuous_query/table_row_update_info.h"
#include "ignite/client/detail/continuous_query/watermark_provider_impl.h"
#include "ignite/client/detail/hybrid_timestamp.h"
#include "ignite/client/detail/table/packed_tuple.h"
#include "ignite/client/detail/table/table_impl.h"
#include "ignite/client/detail/utils.h"
#include "ignite/client/detail/work_thread.h"
#include "ignite/client/ignite_logger.h"
#include "ignite/client/table/ignite_tuple.h"
#include "ignite/common/bytes_view.h"
#include "ignite/common/uuid.h"

#include <cassert>
#include <cstdint>
#include <optional>

namespace ignite::detail {

/**
 * Continuous query scan result.
 */
class continuous_query_scan_result {
public:
    // Default.
    continuous_query_scan_result() = default;

    /**
     * Constructor.
     *
     * @param safe_time Safe time.
     * @param rows Rows.
     */
    continuous_query_scan_result(std::int64_t safe_time, std::vector<table_row_update_info> &&rows)
        : m_safe_time(safe_time)
        , m_rows(std::move(rows)) {}

    /**
     * Get partition safe time.
     *
     * @return Safe time.
     */
    [[nodiscard]] std::int64_t get_safe_time() const { return m_safe_time; }

    /**
     * Get resulting rows.
     *
     * @return Resulting rows.
     */
    [[nodiscard]] std::vector<table_row_update_info> &rows() { return m_rows; }

private:
    /** Partition safe time. */
    std::int64_t m_safe_time{0};

    /** Resulting rows. */
    std::vector<table_row_update_info> m_rows;
};

/**
 * Continuous Query implementation.
 */
class continuous_query_impl : public std::enable_shared_from_this<continuous_query_impl> {
    /**
     * Continuous Query State
     */
    enum class continuous_query_state {
        RUNNING = 0,

        CANCELED,

        FAILED,
    };

public:
    /**
     * Constructor.
     */
    continuous_query_impl(std::shared_ptr<cluster_connection> connection, std::shared_ptr<table_impl> table,
        std::int32_t partitions, continuous_query_options &&options)
        : m_connection(std::move(connection))
        , m_logger(m_connection->get_logger())
        , m_table(std::move(table))
        , m_partitions(partitions)
        , m_options(std::move(options))
        , m_event_types(event_types_to_bitset(m_options.get_event_types()))
        , m_column_names(parse_column_names(m_options.get_column_names())) {
        auto &watermark = m_options.get_watermark();
        if (watermark.has_value() && watermark->m_impl) {
            const auto &impl = *watermark->m_impl;

            if (impl.get_row_ids().size() != std::size_t(m_partitions)) {
                throw ignite_error("Invalid Continuous Query Watermark: row_ids.size="
                    + std::to_string(impl.get_row_ids().size()) + ", partitions=" + std::to_string(m_partitions));
            }

            if (impl.get_timestamps().size() != std::size_t(m_partitions)) {
                throw ignite_error("Invalid Continuous Query Watermark: timestamps.size="
                    + std::to_string(impl.get_timestamps().size()) + ", partitions=" + std::to_string(m_partitions));
            }

            m_lower_bound_row_ids = impl.get_row_ids();
            m_lower_bound_timestamps = impl.get_timestamps();
        } else {
            using namespace std::chrono;

            uuid lowest_row_id{0, 0};
            std::int64_t start_millis = time_point_cast<milliseconds>(system_clock::now()).time_since_epoch().count();

            if (watermark.has_value())
                start_millis = watermark->m_timestamp;

            std::int64_t start_ts = hybrid_timestamp::physical_to_long(start_millis);

            for (std::int32_t part_id = 0; part_id < partitions; ++part_id) {
                m_lower_bound_row_ids.push_back(lowest_row_id);
                m_lower_bound_timestamps.push_back(start_ts);
            }
        }
    }

    /**
     * Destructor.
     */
    virtual ~continuous_query_impl() {
        m_delayed_executor.stop();
        m_delayed_executor.join();
    }

    /**
     * Get next batch of events.
     *
     * @param consumer Events consumer.
     */
    void get_next_async(std::shared_ptr<continuous_query_event_consumer> consumer) {
        assert(consumer != nullptr);
        {
            std::lock_guard<std::recursive_mutex> guard(m_state_mutex);
            if (m_state == continuous_query_state::FAILED) {
                complete_with_error(*consumer, ignite_error{"Continuous query is stopped due to error. You have to"
                    " start a new one if you want to get any new events."});
                return;
            }

            if (m_state == continuous_query_state::CANCELED) {
                complete_with_error(*consumer, ignite_error{"Continuous query canceled"});
                return;
            }
        }

        if (m_watermark_provider) {
            auto part_id = m_watermark_provider->get_partition_id();

            // Invalidating watermark provider.
            m_watermark_provider->mark_inaccessible();
            m_watermark_provider.reset();

            // Updating CQ state for the previous batch (considering it consumed).
            const auto &last_row = m_results[part_id].rows().back();
            m_lower_bound_timestamps[part_id] = last_row.get_timestamp().get_value();
            m_lower_bound_row_ids[part_id] = last_row.get_row_id();
        }

        auto res = result_of_operation<void>([&]() {
            if (m_resume_part_id < 0) {
                make_data_requests(consumer);
            } else {
                get_next_async0(consumer);
            }
        });

        if (res.has_error())
            complete_with_error(*consumer, std::move(res).error());
    }

    /**
     * Check the query for completion.
     *
     * @return @c true if complete.
     */
    [[nodiscard]] bool is_complete() const {
        std::lock_guard<std::recursive_mutex> guard(m_state_mutex);
        return m_state != continuous_query_state::RUNNING;
    }

    /**
     * Cancel the query.
     */
    void cancel() {
        std::lock_guard<std::recursive_mutex> guard(m_state_mutex);
        if (m_state == continuous_query_state::RUNNING) {
            m_state = continuous_query_state::CANCELED;
            m_state_cond.notify_all();
        }
    }

private:
    /**
     * Complete the query and the current call with an error.
     *
     * @param consumer Consumer of the events for the current call.
     */
    void complete_with_error(continuous_query_event_consumer &consumer, ignite_error &&error) {
        {
            std::lock_guard<std::recursive_mutex> guard(m_state_mutex);
            m_state = continuous_query_state::FAILED;
        }

        auto error_reporting_res = result_of_operation<void>([&]() { consumer.complete_with_error(std::move(error)); });

        if (error_reporting_res.has_error() && m_logger) {
            m_logger->log_error("Error while reporting error: " + error_reporting_res.error().what_str()
                + ", Original error: " + error.what_str());
        }
    }

    /**
     * A shared context for a multiple requests that should be handled all together once they all are responded.
     */
    class multi_request_context {
    public:
        // Default
        multi_request_context() = default;

        /**
         * Constructor.
         *
         * @param expected Expected number of records.
         */
        explicit multi_request_context(std::size_t expected)
            : m_expected(expected)
            , m_results(expected) {}

        /**
         * Add new result.
         *
         * @param res Result.
         * @param part_id Partition ID.
         * @return Updated number of expected responses.
         */
        [[nodiscard]] std::size_t add_res(ignite_result<continuous_query_scan_result> &&res, std::int32_t part_id) {
            std::lock_guard<std::recursive_mutex> guard(m_mutex);
            m_results[part_id] = std::move(res).value();
            for (const auto &row : m_results[part_id].rows()) {
                m_schemas.insert(row.get_schema_ver());
            }

            assert(m_expected > 0);

            return --m_expected;
        }

        /**
         * Get schemas.
         *
         * @return Schemas.
         */
        [[nodiscard]] const std::set<std::int32_t> &get_schemas() const {
            std::lock_guard<std::recursive_mutex> guard(m_mutex);
            assert(m_expected == 0);
            return m_schemas;
        }

        /**
         * Get results.
         *
         * @return Results.
         */
        [[nodiscard]] std::vector<continuous_query_scan_result> &&get_results() & {
            std::lock_guard<std::recursive_mutex> guard(m_mutex);
            assert(m_expected == 0);
            return std::move(m_results);
        }

        /**
         * Handle an error, which occurred during the multi-request polling.
         *
         * Function ensures the error is only reported once.
         *
         * @param cq Continuous query instance.
         * @param consumer Events consumer.
         * @param err Error.
         */
        void handle_error(continuous_query_impl &cq, continuous_query_event_consumer &consumer, ignite_error &&err) {
            std::lock_guard<std::recursive_mutex> guard(m_mutex);
            if (!m_error_reported) {
                m_error_reported = true;
                cq.complete_with_error(consumer, std::move(err));
            }
        }

    private:
        /** Mutex. */
        mutable std::recursive_mutex m_mutex;

        /** Error reported. */
        bool m_error_reported{false};

        /** Requests expected. */
        std::size_t m_expected{0};

        /** Results. */
        std::vector<continuous_query_scan_result> m_results;

        /** Schemas used in responses. */
        std::set<std::int32_t> m_schemas;
    };

    /**
     * Read a table row using reader.
     *
     * @param reader Reader to use.
     * @return A table row.
     */
    static std::optional<table_row> read_row(protocol::reader &reader) {
        if (reader.try_read_nil()) {
            return std::nullopt;
        }

        auto bytes = reader.read_binary();

        return table_row{bytes};
    }

    /**
     * Read continuous query scan result.
     *
     * @param reader Reader.
     * @return A single scan result.
     */
    static continuous_query_scan_result read_response(protocol::reader &reader) {
        auto safe_time = reader.read_int64();
        auto schema_ver = reader.read_int32();
        auto cnt = reader.read_int32();

        std::vector<table_row_update_info> rows;
        rows.reserve(cnt);

        for (int i = 0; i < cnt; i++) {
            auto row_uuid = reader.read_uuid();
            auto ts = reader.read_int64();

            auto old_row = read_row(reader);
            auto new_row = read_row(reader);

            auto event_type = static_cast<table_row_event_type>(reader.read_int8());

            rows.emplace_back(schema_ver, row_uuid, hybrid_timestamp{ts}, std::move(new_row), std::move(old_row), event_type);
        }

        return {safe_time, std::move(rows)};
    }

    /**
     * Request data from the cluster.
     *
     * @param consumer Events consumer.
     */
    void make_data_requests(std::shared_ptr<continuous_query_event_consumer> consumer) {
        using namespace std::chrono;

        {
            std::lock_guard<std::recursive_mutex> guard(m_state_mutex);
            if (m_state != continuous_query_state::RUNNING) {
                complete_with_error(*consumer, ignite_error{"Continuous query canceled"});
                return;
            }
        }

        auto now = steady_clock::now();
        if (duration_cast<milliseconds>(now - m_last_poll).count() < m_options.get_poll_interval_ms()) {
            m_delayed_executor.add_job([this, consumer = std::move(consumer)]() mutable {
                std::unique_lock<std::recursive_mutex> guard(m_state_mutex);
                auto wait_until = m_last_poll + milliseconds(m_options.get_poll_interval_ms());
                m_state_cond.wait_until(guard, wait_until);
                if (m_state == continuous_query_state::RUNNING) {
                    make_data_requests(std::move(consumer));
                }
            });
            return;
        }

        m_last_poll = now;

        auto context = std::make_shared<multi_request_context>(std::size_t(m_partitions));
        for (int part_id = 0; part_id < m_partitions; ++part_id) {
            auto write_func = [this, part_id](protocol::writer &writer, auto&) {
                writer.write(m_table->get_id());
                writer.write(part_id);
                writer.write(m_lower_bound_timestamps[part_id]);
                writer.write(m_lower_bound_row_ids[part_id]);
                writer.write(m_options.get_page_size());
                writer.write(m_event_types);

                if (m_column_names.empty()) {
                    writer.write_nil();
                } else {
                    writer.write(std::int32_t(m_column_names.size()));

                    for (const auto &col_name : m_column_names) {
                        writer.write(col_name);
                    }
                }
            };

            auto self = shared_from_this();
            auto req_callback = [context, self, part_id, consumer](
                                    ignite_result<continuous_query_scan_result> &&res) mutable {
                if (res.has_error()) {
                    context->handle_error(*self, *consumer, std::move(res).error());
                    return;
                }

                if (self->m_state != continuous_query_state::RUNNING) {
                    context->handle_error(
                        *self, *consumer, ignite_error{"Continuous query request execution has been canceled"});
                    return;
                }

                std::size_t left = context->add_res(std::move(res), part_id);
                if (left == 0) {
                    // The last response was received.
                    // The code below is only executed once and not concurrently.
                    self->m_table->load_schemas_async(
                        &context->get_schemas(), [self, context, consumer = std::move(consumer)](auto res) {
                            if (res.has_error()) {
                                context->handle_error(*self, *consumer, std::move(res).error());
                                return;
                            }

                            auto handling_res = result_of_operation<void>([&]() {
                                self->m_results = context->get_results();
                                self->m_resume_part_id = 0;
                                self->get_next_async0(consumer);
                            });

                            if (handling_res.has_error()) {
                                context->handle_error(*self, *consumer, std::move(res).error());
                            }
                        });
                }
            };

            m_connection->perform_request<continuous_query_scan_result>(
                protocol::client_operation::CONTINUOUS_QUERY_SCAN, nullptr, write_func, read_response, req_callback);
        }
    }

    /**
     * Iterate over cached data from the specified position.
     *
     * @param consumer Events consumer.
     */
    void get_next_async0(const std::shared_ptr<continuous_query_event_consumer> &consumer) {
        assert(m_resume_part_id >= 0 && m_resume_part_id < m_partitions);

        for (auto part_id = m_resume_part_id; part_id < m_partitions; ++part_id) {
            auto &result = m_results[part_id];

            auto &rows = result.rows();
            if (rows.empty()) {
                // When there are no results, lower_bound_ts is set to safe_time of the partition.
                if (result.get_safe_time() > m_lower_bound_timestamps[part_id]) {
                    m_lower_bound_timestamps[part_id] = result.get_safe_time();
                    m_lower_bound_row_ids[part_id] = {};
                }
                continue;
            }

            // Pass the current CQ state in the form of row_ids and timestamps.
            // Those arrays are mutable, therefore accessible only during the on_next call.
            // This way we don't have to clone them unless requested by the user.
            m_watermark_provider = std::make_shared<watermark_provider_impl>(
                part_id, m_lower_bound_row_ids, m_lower_bound_timestamps, rows);

            for (std::int32_t row_idx = 0; row_idx < std::int32_t(rows.size()); ++row_idx) {
                table_row_update_info &row = rows.at(row_idx);
                auto sch = m_table->get_schema(row.get_schema_ver());

                auto entry = table_row_to_tuple(sch, row.move_row());
                auto old_entry = table_row_to_tuple(std::move(sch), row.move_old_row());

                m_lower_bound_timestamps[part_id] = row.get_timestamp().get_value();
                m_lower_bound_row_ids[part_id] = row.get_row_id();

                consumer->handle_entry(
                    row_idx,
                    std::move(entry),
                    std::move(old_entry),
                    row.get_event_type(),
                    m_watermark_provider
                );
            }

            auto resume_part_id = part_id + 1;

            m_resume_part_id = resume_part_id == m_partitions ? -1 : resume_part_id;

            consumer->complete();
            return;
        }
        if (m_options.get_enable_empty_batches()) {
            consumer->complete_empty(
                std::make_shared<watermark_provider_impl>(m_lower_bound_row_ids, m_lower_bound_timestamps));
        }

        // We processed all responses and found no updates. Requesting data again.
        m_resume_part_id = 0;
        make_data_requests(consumer);
    }

    /**
     * Convert table row to a tuple.
     *
     * @param sch Schema.
     * @return Ignite tuple.
     */
    static std::optional<packed_tuple> table_row_to_tuple(
        std::shared_ptr<schema> sch, const std::optional<table_row> &row) {
        if (!row.has_value()) {
            return std::nullopt;
        }

        return {{row->get_data(), std::move(sch)}};
    }

    /**
     * Encode event types into bitmask.
     *
     * @param events Event set.
     * @return Bitmask.
     */
    static std::int8_t event_types_to_bitset(const std::set<table_row_event_type> &events) {
        std::int8_t res{0};
        for (auto event : events) {
            res = std::int8_t(res | (1 << int(event)));
        }
        return res;
    }

    /**
     * Parse column names.
     *
     * @param column_names Column names to parse.
     * @return Parsed column names.
     */
    static std::vector<std::string> parse_column_names(const std::set<std::string> &column_names) {
        std::vector<std::string> res;
        res.reserve(column_names.size());

        for (const auto &column_name : column_names) {
            res.push_back(parse_column_name(column_name));
        }
        return res;
    }

    /** State mutex. */
    mutable std::recursive_mutex m_state_mutex;

    /** State conditional. */
    mutable std::condition_variable_any m_state_cond;

    /** State. */
    continuous_query_state m_state{continuous_query_state::RUNNING};

    /** Connection. */
    std::shared_ptr<cluster_connection> m_connection;

    /** Logger. */
    std::shared_ptr<ignite_logger> m_logger;

    /** Table. */
    std::shared_ptr<table_impl> m_table;

    /** Number of partitions. */
    const std::int32_t m_partitions{0};

    /** Options. */
    const continuous_query_options m_options;

    /** Event types mask. */
    const std::int8_t m_event_types{0};

    /** Columns to read. */
    const std::vector<std::string> m_column_names;

    /** Cached results of the last request. */
    std::vector<continuous_query_scan_result> m_results;

    /** Lower bound IDs. */
    std::vector<uuid> m_lower_bound_row_ids;

    /** Lower bound timestamps. */
    std::vector<std::int64_t> m_lower_bound_timestamps;

    /** Resume partition ID. */
    std::int32_t m_resume_part_id{-1};

    /** Actual watermark provider. */
    std::shared_ptr<watermark_provider_impl> m_watermark_provider;

    /** Last poll timestamp. */
    std::chrono::time_point<std::chrono::steady_clock> m_last_poll;

    /** Delayed executor. */
    work_thread m_delayed_executor;
};

} // namespace ignite::detail
