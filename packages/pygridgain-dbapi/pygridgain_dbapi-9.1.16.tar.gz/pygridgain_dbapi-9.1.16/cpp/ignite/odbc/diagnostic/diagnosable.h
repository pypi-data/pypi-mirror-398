/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/ignite_error.h"
#include "ignite/odbc/diagnostic/diagnostic_record_storage.h"
#include "ignite/odbc/odbc_error.h"

#include <functional>

namespace ignite {

class odbc_error;

/**
 * diagnosable interface.
 */
class diagnosable {
public:
    // Default
    virtual ~diagnosable() = default;

    /**
     * Get diagnostic record.
     *
     * @return Diagnostic record.
     */
    [[nodiscard]] virtual const diagnostic_record_storage &get_diagnostic_records() const = 0;

    /**
     * Get diagnostic record.
     *
     * @return Diagnostic record.
     */
    [[nodiscard]] virtual diagnostic_record_storage &get_diagnostic_records() = 0;

    /**
     * Add new status record.
     *
     * @param sql_state SQL state.
     * @param message Message.
     * @param row_num Associated row number.
     * @param column_num Associated column number.
     */
    virtual void add_status_record(
        sql_state sql_state, const std::string &message, int32_t row_num, int32_t column_num) = 0;

    /**
     * Add new status record.
     *
     * @param sql_state SQL state.
     * @param message Message.
     */
    virtual void add_status_record(sql_state sql_state, const std::string &message) = 0;

    /**
     * Add new status record.
     *
     * @param err Error.
     */
    virtual void add_status_record(const odbc_error &err) = 0;

    /**
     * Add new status record.
     *
     * @param rec Record.
     */
    virtual void add_status_record(const diagnostic_record &rec) = 0;

    /**
     * Catch and handle any known errors that can happen in function.
     *
     * @param func Code to handle.
     * @return @c true if no error happened and false otherwise.
     */
    bool catch_errors(const std::function<void()> &func) {
        try {
            func();
        } catch (const odbc_error &err) {
            add_status_record(err);
            return false;
        } catch (const ignite_error &err) {
            add_status_record(error_code_to_sql_state(err.get_status_code()), err.what_str());
            return false;
        }

        return true;
    }

protected:
    // Default
    diagnosable() = default;
};

} // namespace ignite
