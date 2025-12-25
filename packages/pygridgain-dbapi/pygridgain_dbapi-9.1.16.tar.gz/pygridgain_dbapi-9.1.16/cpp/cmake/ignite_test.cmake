#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

# ignite_test(<test-name> [DISCOVER] SOURCES <test-src>... [LIBS <lib>...])
#
# Function to add a unit test.
function(ignite_test TEST_NAME)
    if (NOT ${ENABLE_TESTS})
        return()
    endif()

    if (MSVC)
        add_compile_options(/bigobj)
    endif()

    set(OPTIONAL_ARGUMENT_TAGS DISCOVER)
    set(SINGLE_ARGUMENT_TAGS)
    set(MULTI_ARGUMENT_TAGS LIBS SOURCES)

    cmake_parse_arguments(IGNITE_TEST
            "${OPTIONAL_ARGUMENT_TAGS}"
            "${SINGLE_ARGUMENT_TAGS}"
            "${MULTI_ARGUMENT_TAGS}"
            ${ARGN})

    add_executable(${TEST_NAME} ${IGNITE_TEST_SOURCES})

    target_link_libraries(${TEST_NAME} ${IGNITE_TEST_LIBS} GTest::gtest_main GTest::gmock_main)

    if(${IGNITE_TEST_DISCOVER})
        gtest_discover_tests(${TEST_NAME} XML_OUTPUT_DIR ${CMAKE_BINARY_DIR}/Testing/Result)
    endif()
endfunction()
