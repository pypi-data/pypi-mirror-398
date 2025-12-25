/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/odbc/diagnostic/diagnosable_adapter.h"
#include "ignite/odbc/log.h"
#include "ignite/odbc/odbc_error.h"

namespace ignite {

void diagnosable_adapter::add_status_record(
    sql_state sql_state, const std::string &message, int32_t row_num, int32_t column_num) {
    LOG_MSG("Adding new record: " << message << ", row_num: " << row_num << ", column_num: " << column_num);
    m_diagnostic_records.add_status_record(diagnostic_record(sql_state, message, "", "", row_num, column_num));
}

void diagnosable_adapter::add_status_record(sql_state sql_state, const std::string &message) {
    add_status_record(sql_state, message, 0, 0);
}

void diagnosable_adapter::add_status_record(const std::string &message) {
    add_status_record(sql_state::SHY000_GENERAL_ERROR, message);
}

void diagnosable_adapter::add_status_record(const odbc_error &err) {
    add_status_record(err.get_state(), err.get_error_message(), 0, 0);
}

void diagnosable_adapter::add_status_record(const diagnostic_record &rec) {
    LOG_MSG("Adding new record: " << rec.get_sql_state() << " " << rec.get_message_text());
    m_diagnostic_records.add_status_record(rec);
}

} // namespace ignite
