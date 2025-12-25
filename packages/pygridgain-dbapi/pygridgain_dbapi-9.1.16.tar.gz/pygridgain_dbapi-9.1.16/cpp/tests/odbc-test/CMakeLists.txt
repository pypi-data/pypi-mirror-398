#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

project(ignite-odbc-test)

set(TARGET ${PROJECT_NAME})

find_package(ODBC REQUIRED)

set(SOURCES
    api_robustness_test.cpp
    auth_test.cpp
    connection_test.cpp
    error_test.cpp
    main.cpp
    many_cursors_test.cpp
    meta_queries_test.cpp
    queries_test.cpp
    ssl_test.cpp
    timeout_test.cpp
    transaction_test.cpp
)

ignite_test(${TARGET} SOURCES ${SOURCES} LIBS ignite-test-common ignite3-client-static ${ODBC_LIBRARY})

if (WIN32)
    remove_definitions(-DUNICODE=1)
endif()
