/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/detail/table/tables_impl.h"
#include "ignite/client/detail/table/table_impl.h"

#include <ignite/protocol/reader.h>
#include <ignite/protocol/writer.h>

namespace {
using namespace ignite;

qualified_name unpack_qualified_name(protocol::reader &reader, const protocol::protocol_context &context) {
    if (context.is_feature_supported(protocol::bitmask_feature::TABLE_REQS_USE_QUALIFIED_NAME)) {
        auto schema_name = reader.read_string();
        auto object_name = reader.read_string();

        return qualified_name::create(schema_name, object_name);
    }

    auto canonical_name = reader.read_string();
    return qualified_name::parse(canonical_name);
}

}

namespace ignite::detail {

void tables_impl::get_table_async(std::string_view name, ignite_callback<std::optional<table>> callback) {
    get_table_async(qualified_name::parse(name), callback);
}

void tables_impl::get_table_async(const qualified_name &name, ignite_callback<std::optional<table>> callback) {
    auto writer_func = [&name](protocol::writer &writer, const protocol::protocol_context &context) {
        if (context.is_feature_supported(protocol::bitmask_feature::TABLE_REQS_USE_QUALIFIED_NAME)) {
            writer.write(name.get_schema_name());
            writer.write(name.get_object_name());
        } else {
            writer.write(name.get_object_name());
        }
    };

    auto reader_func = [conn = m_connection](protocol::reader &reader,
        std::shared_ptr<node_connection> n_conn) mutable -> std::optional<table> {
        if (reader.try_read_nil())
            return std::nullopt;

        auto id = reader.read_int32();

        auto actual_name = unpack_qualified_name(reader, n_conn->get_protocol_context());
        auto table0 = std::make_shared<table_impl>(std::move(actual_name), id, std::move(conn));

        return std::make_optional(table(table0));
    };

    const auto operation_func = [](const protocol::protocol_context &context) -> protocol::client_operation {
        return context.is_feature_supported(protocol::bitmask_feature::TABLE_REQS_USE_QUALIFIED_NAME)
            ? protocol::client_operation::TABLE_GET_QUALIFIED
            : protocol::client_operation::TABLE_GET;
    };

    m_connection->perform_request<std::optional<table>>(
        operation_func, writer_func, std::move(reader_func), std::move(callback));
}

void tables_impl::get_tables_async(ignite_callback<std::vector<table>> callback) {
    auto reader_func = [conn = m_connection](protocol::reader &reader,
        std::shared_ptr<node_connection> n_conn) -> std::vector<table> {
        if (reader.try_read_nil())
            return {};

        std::vector<table> tables;
        auto size = reader.read_int32();
        tables.reserve(size);

        for (std::int32_t table_idx = 0; table_idx < size; ++table_idx) {
            auto id = reader.read_int32();
            auto name = unpack_qualified_name(reader, n_conn->get_protocol_context());
            tables.emplace_back(table{std::make_shared<table_impl>(std::move(name), id, conn)});
        }
        return tables;
    };

    const auto operation_func = [](const protocol::protocol_context &context) -> protocol::client_operation {
        return context.is_feature_supported(protocol::bitmask_feature::TABLE_REQS_USE_QUALIFIED_NAME)
            ? protocol::client_operation::TABLES_GET_QUALIFIED
            : protocol::client_operation::TABLES_GET;
    };

    m_connection->perform_request<std::vector<table>>(
        operation_func, [](auto&, auto&){}, std::move(reader_func), std::move(callback));
}

} // namespace ignite::detail
