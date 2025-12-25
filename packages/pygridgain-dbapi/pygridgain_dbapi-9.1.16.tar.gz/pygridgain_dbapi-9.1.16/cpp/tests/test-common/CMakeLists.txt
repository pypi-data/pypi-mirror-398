#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

project(ignite-test-common)

set(TARGET ${PROJECT_NAME})

set(SOURCES
    basic_auth_test_suite.h
    cmd_process.h
    ignite_runner.cpp ignite_runner.h
    process.cpp
    test_utils.cpp test_utils.h
    hidden_param.h
)

add_library(${TARGET} OBJECT ${SOURCES})
target_link_libraries(${TARGET} ignite-common)
target_include_directories(${TARGET} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

set_target_properties(${TARGET} PROPERTIES VERSION ${CMAKE_PROJECT_VERSION})
set_target_properties(${TARGET} PROPERTIES POSITION_INDEPENDENT_CODE 1)
