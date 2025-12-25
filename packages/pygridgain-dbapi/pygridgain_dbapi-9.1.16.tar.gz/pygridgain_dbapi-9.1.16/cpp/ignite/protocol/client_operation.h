/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

namespace ignite::protocol {

/**
 * Client operation code.
 */
enum class client_operation {
    /** Heartbeat. */
    HEARTBEAT = 1,

    /** Get all tables. */
    TABLES_GET = 3,

    /** Get table. */
    TABLE_GET = 4,

    /** Get schemas. */
    SCHEMAS_GET = 5,

    /** Upsert tuple. */
    TUPLE_UPSERT = 10,

    /** Get tuple. */
    TUPLE_GET = 12,

    /** Upsert all tuples. */
    TUPLE_UPSERT_ALL = 13,

    /** Get all tuples. */
    TUPLE_GET_ALL = 15,

    /** Get and upsert tuple. */
    TUPLE_GET_AND_UPSERT = 16,

    /** Insert tuple. */
    TUPLE_INSERT = 18,

    /** Insert all tuples. */
    TUPLE_INSERT_ALL = 20,

    /** Replace tuple. */
    TUPLE_REPLACE = 22,

    /** Replace exact tuple. */
    TUPLE_REPLACE_EXACT = 24,

    /** Get and replace tuple. */
    TUPLE_GET_AND_REPLACE = 26,

    /** Delete tuple. */
    TUPLE_DELETE = 28,

    /** Delete all tuples. */
    TUPLE_DELETE_ALL = 29,

    /** Delete exact tuple. */
    TUPLE_DELETE_EXACT = 30,

    /** Delete all exact tuples. */
    TUPLE_DELETE_ALL_EXACT = 31,

    /** Get and delete tuple. */
    TUPLE_GET_AND_DELETE = 32,

    /** Contains tuple. */
    TUPLE_CONTAINS_KEY = 33,

    /** Get table metadata. */
    JDBC_TABLE_META = 38,

    /** Get column metadata. */
    JDBC_COLUMN_META = 39,

    /** Get primary key metadata. */
    JDBC_PK_META = 41,

    /** Begin transaction. */
    TX_BEGIN = 43,

    /** Commit transaction. */
    TX_COMMIT = 44,

    /** Rollback transaction. */
    TX_ROLLBACK = 45,

    /** Execute compute job. */
    COMPUTE_EXECUTE = 47,

    /** Get cluster nodes. */
    CLUSTER_GET_NODES = 48,

    /** Execute compute job. */
    COMPUTE_EXECUTE_COLOCATED = 49,

    /** Execute SQL query. */
    SQL_EXEC = 50,

    /** Get the next page. */
    SQL_CURSOR_NEXT_PAGE = 51,

    /** Close the cursor. */
    SQL_CURSOR_CLOSE = 52,

    /** Get partition assignment. */
    PARTITION_ASSIGNMENT_GET = 53,

    /** Execute SQL script. */
    SQL_EXEC_SCRIPT = 56,

    /** SQL query metadata. */
    SQL_QUERY_META = 57,

    /** Get compute job status. */
    COMPUTE_GET_STATUS = 59,

    /** Cancel compute job. */
    COMPUTE_CANCEL = 60,

    /** Change compute job priority. */
    COMPUTE_CHANGE_PRIORITY = 61,

    /** Execute SQL query with the parameter batch. */
    SQL_EXEC_BATCH = 63,

    /** Cancel execution of an SQL query previously initiated on the same connection. */
    SQL_CANCEL_EXEC = 70,

    /** Get tables with qualified names. */
    TABLES_GET_QUALIFIED = 71,

    /** Get table by qualified name. */
    TABLE_GET_QUALIFIED = 72,

    /** Scan partition for continuous query. */
    CONTINUOUS_QUERY_SCAN = 1001,

    /** Create or get map by name. */
    MAP_GET_OR_CREATE = 1007,
};

} // namespace ignite::protocol
