/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "detail/thread_timer.h"
#include "ignite/odbc/diagnostic/diagnosable_adapter.h"

#include <set>

namespace ignite {
class sql_connection;

/**
 * ODBC environment.
 */
class sql_environment : public diagnosable_adapter {
public:
    /** Pointer to the connection. */
    using sql_connection_ptr = std::shared_ptr<sql_connection>;

    /** Connection set type. */
    using connection_set = std::set<sql_connection *>;

    // Delete
    sql_environment(sql_environment &&) = delete;
    sql_environment(const sql_environment &) = delete;
    sql_environment &operator=(sql_environment &&) = delete;
    sql_environment &operator=(const sql_environment &) = delete;

    // Default
    sql_environment();

    /**
     * Create connection associated with the environment.
     *
     * @return Pointer to valid instance on success or NULL on failure.
     */
    sql_connection_ptr *create_connection();

    /**
     * Deregister connection.
     *
     * @param conn Connection to deregister.
     */
    void deregister_connection(sql_connection *conn);

    /**
     * Perform transaction commit on all the associated connections.
     */
    void transaction_commit();

    /**
     * Perform transaction rollback on all the associated connections.
     */
    void transaction_rollback();

    /**
     * Set attribute.
     *
     * @param attr Attribute to set.
     * @param value Value.
     * @param len Value length if the attribute is of string type.
     */
    void set_attribute(int32_t attr, void *value, int32_t len);

    /**
     * Get attribute.
     *
     * @param attr Attribute to set.
     * @param buffer Buffer to put value to.
     */
    void get_attribute(int32_t attr, application_data_buffer &buffer);

private:
    /**
     * Create connection associated with the environment.
     * Internal call.
     *
     * @return Pointer to valid instance on success or NULL on failure.
     * @return Operation result.
     */
    sql_result internal_create_connection(sql_connection_ptr *&connection);

    /**
     * Perform transaction commit on all the associated connections.
     * Internal call.
     *
     * @return Operation result.
     */
    sql_result internal_transaction_commit();

    /**
     * Perform transaction rollback on all the associated connections.
     * Internal call.
     *
     * @return Operation result.
     */
    sql_result internal_transaction_rollback();

    /**
     * Set attribute.
     * Internal call.
     *
     * @param attr Attribute to set.
     * @param value Value.
     * @param len Value length if the attribute is of string type.
     * @return Operation result.
     */
    sql_result internal_set_attribute(int32_t attr, void *value, int32_t len);

    /**
     * Get attribute.
     * Internal call.
     *
     * @param attr Attribute to set.
     * @param buffer Buffer to put value to.
     * @return Operation result.
     */
    sql_result internal_get_attribute(int32_t attr, application_data_buffer &buffer);

    /** Associated connections. */
    connection_set m_connections;

    /** ODBC version. */
    int32_t m_odbc_version{SQL_OV_ODBC3_80};

    /** ODBC null-termination of string behaviour. */
    int32_t m_odbc_nts{SQL_TRUE};

    /** Timer thread. */
    std::shared_ptr<detail::thread_timer> m_timer_thread;
};

} // namespace ignite
