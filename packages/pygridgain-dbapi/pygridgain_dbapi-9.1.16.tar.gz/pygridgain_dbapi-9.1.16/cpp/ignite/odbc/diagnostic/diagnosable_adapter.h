/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/odbc/diagnostic/diagnosable.h"

#define IGNITE_ODBC_API_CALL(...)                                                                                      \
 m_diagnostic_records.reset();                                                                                         \
 sql_result result = (__VA_ARGS__);                                                                                    \
 m_diagnostic_records.set_header_record(result)

#define IGNITE_ODBC_API_CALL_ALWAYS_SUCCESS                                                                            \
 m_diagnostic_records.reset();                                                                                         \
 m_diagnostic_records.set_header_record(sql_result::AI_SUCCESS)

namespace ignite {
class odbc_error;

/**
 * Diagnosable interface.
 */
class diagnosable_adapter : public diagnosable {
public:
    // Default
    diagnosable_adapter() = default;

    /**
     * Get diagnostic record.
     *
     * @return Diagnostic record.
     */
    [[nodiscard]] const diagnostic_record_storage &get_diagnostic_records() const override {
        return m_diagnostic_records;
    }

    /**
     * Get diagnostic record.
     *
     * @return Diagnostic record.
     */
    [[nodiscard]] diagnostic_record_storage &get_diagnostic_records() override { return m_diagnostic_records; }

    /**
     * Add new status record.
     *
     * @param sql_state SQL state.
     * @param message Message.
     * @param row_num Associated row number.
     * @param column_num Associated column number.
     */
    void add_status_record(
        sql_state sql_state, const std::string &message, int32_t row_num, int32_t column_num) override;

    /**
     * Add new status record.
     *
     * @param sql_state SQL state.
     * @param message Message.
     */
    void add_status_record(sql_state sql_state, const std::string &message) override;

    /**
     * Add new status record with sql_state::SHY000_GENERAL_ERROR state.
     *
     * @param message Message.
     */
    void add_status_record(const std::string &message);

    /**
     * Add new status record.
     *
     * @param err Error.
     */
    void add_status_record(const odbc_error &err) override;

    /**
     * Add new status record.
     *
     * @param rec Record.
     */
    void add_status_record(const diagnostic_record &rec) override;

protected:
    /** Diagnostic records. */
    diagnostic_record_storage m_diagnostic_records;
};

} // namespace ignite
