/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include <utility>

#include "ignite/odbc/query/foreign_keys_query.h"
#include "ignite/odbc/type_traits.h"

namespace ignite {

foreign_keys_query::foreign_keys_query(diagnosable_adapter &m_diag, std::string primary_catalog,
    std::string primary_schema, std::string primary_table, std::string foreign_catalog, std::string foreign_schema,
    std::string foreign_table)
    : query(m_diag, query_type::FOREIGN_KEYS)
    , m_primary_catalog(std::move(primary_catalog))
    , m_primary_schema(std::move(primary_schema))
    , m_primary_table(std::move(primary_table))
    , m_foreign_catalog(std::move(foreign_catalog))
    , m_foreign_schema(std::move(foreign_schema))
    , m_foreign_table(std::move(foreign_table)) {
    m_columns_meta.reserve(14);

    const std::string sch;
    const std::string tbl;

    m_columns_meta.emplace_back(sch, tbl, "PKTABLE_CAT", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "PKTABLE_SCHEM", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "PKTABLE_NAME", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "PKCOLUMN_NAME", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "FKTABLE_CAT", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "FKTABLE_SCHEM", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "FKTABLE_NAME", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "FKCOLUMN_NAME", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "KEY_SEQ", ignite_type::INT16);
    m_columns_meta.emplace_back(sch, tbl, "UPDATE_RULE", ignite_type::INT16);
    m_columns_meta.emplace_back(sch, tbl, "DELETE_RULE", ignite_type::INT16);
    m_columns_meta.emplace_back(sch, tbl, "FK_NAME", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "PK_NAME", ignite_type::STRING);
    m_columns_meta.emplace_back(sch, tbl, "DEFERRABILITY", ignite_type::INT16);
}

sql_result foreign_keys_query::execute() {
    m_executed = true;

    return sql_result::AI_SUCCESS;
}

sql_result foreign_keys_query::fetch_next_row(column_binding_map &) {
    if (!m_executed) {
        m_diag.add_status_record(sql_state::SHY010_SEQUENCE_ERROR, "Query was not executed.");

        return sql_result::AI_ERROR;
    }

    return sql_result::AI_NO_DATA;
}

sql_result foreign_keys_query::get_column(std::uint16_t, application_data_buffer &) {
    if (!m_executed) {
        m_diag.add_status_record(sql_state::SHY010_SEQUENCE_ERROR, "Query was not executed.");

        return sql_result::AI_ERROR;
    }

    return sql_result::AI_NO_DATA;
}

sql_result foreign_keys_query::close() {
    m_executed = false;

    return sql_result::AI_SUCCESS;
}

} // namespace ignite
