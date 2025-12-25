/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "odbc_suite.h"

#include <gmock/gmock-matchers.h>
#include <gtest/gtest.h>

using namespace ignite;

/**
 * Test setup fixture.
 */
struct error_test : public odbc_suite {
public:
    static void SetUpTestSuite() {
        odbc_connection conn;
        conn.odbc_connect(get_basic_connection_string());

        auto table_avail = conn.wait_for_table(TABLE_NAME_ALL_COLUMNS_SQL, std::chrono::seconds(10));
        if (!table_avail) {
            FAIL() << "Table '" + TABLE_NAME_ALL_COLUMNS_SQL + "' is not available";
        }

        SQLRETURN ret = conn.exec_query("DELETE FROM " + TABLE_NAME_ALL_COLUMNS_SQL);
        if (!SQL_SUCCEEDED(ret)) {
            FAIL() << conn.get_statement_error_message();
        }
    }

    void SetUp() override {
        odbc_connect(get_basic_connection_string());
        exec_query("DELETE FROM " + TABLE_NAME_ALL_COLUMNS_SQL);
        odbc_clean_up();
    }
};

TEST_F(error_test, connect_fail) {
    prepare_environment();

    // Connect string
    auto connect_str = to_sqlchar("driver={" + DRIVER_NAME + "};ADDRESS=127.0.0.1:1111");

    SQLCHAR out_str[ODBC_BUFFER_SIZE];
    SQLSMALLINT out_str_len;

    // Connecting to ODBC server.
    SQLRETURN ret = SQLDriverConnect(m_conn, NULL, connect_str.data(), SQLSMALLINT(connect_str.size()), out_str,
        sizeof(out_str), &out_str_len, SQL_DRIVER_COMPLETE);

    ASSERT_EQ(ret, SQL_ERROR);
    EXPECT_EQ(get_odbc_error_state(SQL_HANDLE_DBC, m_conn), "08001");
}

TEST_F(error_test, duplicate_key) {
    odbc_connect(get_basic_connection_string());

    SQLCHAR insert_req[] = "INSERT INTO tbl_all_columns_sql(key, str) VALUES(1, 'some')";

    SQLRETURN ret;

    ret = SQLExecDirect(m_statement, insert_req, SQL_NTS);
    ODBC_FAIL_ON_ERROR(ret, SQL_HANDLE_STMT, m_statement);

    ret = SQLExecDirect(m_statement, insert_req, SQL_NTS);

    ASSERT_EQ(ret, SQL_ERROR);
    EXPECT_EQ(get_odbc_error_state(SQL_HANDLE_STMT, m_statement), "23000");
}

TEST_F(error_test, update_key) {
    odbc_connect(get_basic_connection_string());

    SQLCHAR insert_req[] = "INSERT INTO tbl_all_columns_sql(key, str) VALUES(1, 'some')";

    SQLRETURN ret;

    ret = SQLExecDirect(m_statement, insert_req, SQL_NTS);
    ODBC_FAIL_ON_ERROR(ret, SQL_HANDLE_STMT, m_statement);

    SQLCHAR update_req[] = "UPDATE TestType SET _key=2 WHERE _key=1";

    ret = SQLExecDirect(m_statement, update_req, SQL_NTS);

    ASSERT_EQ(ret, SQL_ERROR);
    // TODO: IGNITE-21217 Check STMT_VALIDATION error code usage
    EXPECT_EQ(get_odbc_error_state(SQL_HANDLE_STMT, m_statement), "42000");
}

TEST_F(error_test, table_not_found) {
    odbc_connect(get_basic_connection_string());

    SQLCHAR req[] = "DROP TABLE Nonexisting";

    SQLRETURN ret;

    ret = SQLExecDirect(m_statement, req, SQL_NTS);

    ASSERT_EQ(ret, SQL_ERROR);
    // TODO: IGNITE-21217 Check STMT_VALIDATION error code usage
    EXPECT_EQ(get_odbc_error_state(SQL_HANDLE_STMT, m_statement), "42000");

    std::string error = get_odbc_error_message(SQL_HANDLE_STMT, m_statement);
    EXPECT_THAT(error, testing::HasSubstr("Table with name 'PUBLIC.NONEXISTING' not found"));
}

TEST_F(error_test, object_not_found_message) {
    odbc_connect(get_basic_connection_string());

    SQLCHAR select_req[] = "SELECT a FROM B";

    SQLRETURN ret = SQLExecDirect(m_statement, select_req, sizeof(select_req));

    ASSERT_EQ(ret, SQL_ERROR);

    std::string error = get_odbc_error_message(SQL_HANDLE_STMT, m_statement);

    EXPECT_THAT(error, testing::HasSubstr("Object 'B' not found"));
}

TEST_F(error_test, index_not_found) {
    odbc_connect(get_basic_connection_string());

    SQLCHAR req[] = "DROP INDEX Nonexisting";

    SQLRETURN ret;

    ret = SQLExecDirect(m_statement, req, SQL_NTS);

    ASSERT_EQ(ret, SQL_ERROR);
    // TODO: IGNITE-21217 Check STMT_VALIDATION error code usage
    EXPECT_EQ(get_odbc_error_state(SQL_HANDLE_STMT, m_statement), "42000");
}

TEST_F(error_test, syntax_error) {
    odbc_connect(get_basic_connection_string());

    SQLCHAR req[] = "INSERT INTO tbl_all_columns_sql(key, non_existing) VALUES(1, 'some')";

    SQLRETURN ret;

    ret = SQLExecDirect(m_statement, req, SQL_NTS);

    ASSERT_EQ(ret, SQL_ERROR);
    // TODO: IGNITE-21217 Check STMT_VALIDATION error code usage
    EXPECT_EQ(get_odbc_error_state(SQL_HANDLE_STMT, m_statement), "42000");
}
