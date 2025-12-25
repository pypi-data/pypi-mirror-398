#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

project(ignite-client-test)

set(TARGET ${PROJECT_NAME})

set(SOURCES
    basic_authenticator_test.cpp
    column_order_test.cpp
    compute_test.cpp
    continuous_query_test.cpp
    ignite_client_test.cpp
    ignite_runner_suite.h
    key_value_binary_view_test.cpp
    key_value_view_test.cpp
    main.cpp
    record_binary_view_test.cpp
    record_view_test.cpp
    schema_synchronization_test.cpp
    sql_test.cpp
    ssl_test.cpp
    tables_test.cpp
    transactions_test.cpp
)

ignite_test(${TARGET} SOURCES ${SOURCES} LIBS ignite-test-common ignite3-client)
