#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

project(ignite3-odbc)

set(TARGET ${PROJECT_NAME})

include(find_odbc)
find_package(ODBC REQUIRED)

set(SOURCES
    app/application_data_buffer.cpp
    app/parameter.cpp
    app/parameter_set.cpp
    common_types.cpp
    config/config_tools.cpp
    config/configuration.cpp
    config/connection_info.cpp
    diagnostic/diagnosable_adapter.cpp
    diagnostic/diagnostic_record.cpp
    diagnostic/diagnostic_record_storage.cpp
    meta/table_meta.cpp
    query/column_metadata_query.cpp
    query/data_query.cpp
    query/foreign_keys_query.cpp
    query/primary_keys_query.cpp
    query/special_columns_query.cpp
    query/table_metadata_query.cpp
    query/type_info_query.cpp
    odbc.cpp
    entry_points.cpp
    ssl_mode.cpp
    sql_connection.cpp
    sql_environment.cpp
    sql_statement.cpp
    type_traits.cpp
    utility.cpp
    log.cpp
)

set(EXTRA_FILES)

if (WIN32)
    string(REPLACE "." "," CMAKE_PROJECT_VERSION_COMMAS ${CMAKE_PROJECT_VERSION})
    configure_file(${CMAKE_CURRENT_SOURCE_DIR}/version.rc.in ${CMAKE_CURRENT_BINARY_DIR}/version.rc @ONLY)
    set(EXTRA_FILES ${CMAKE_CURRENT_BINARY_DIR}/version.rc)
endif()

add_compile_definitions(CMAKE_PROJECT_VERSION="${CMAKE_PROJECT_VERSION}")

add_library(${TARGET}-obj OBJECT ${SOURCES})
target_include_directories(${TARGET}-obj PUBLIC ${CMAKE_CURRENT_SOURCE_DIR} ${ODBC_INCLUDE_DIRS})

add_library(${TARGET} SHARED $<TARGET_OBJECTS:${TARGET}-obj> module.def ${EXTRA_FILES})

set(LIBRARIES
    ignite-common
    ignite-tuple
    ignite-network
    ignite-protocol
    ${ODBC_LIBRARIES}
)

set(_target_libs ${TARGET} ${TARGET}-obj)

foreach(_target_lib IN LISTS _target_libs)
    set_target_properties(${_target_lib} PROPERTIES VERSION ${CMAKE_PROJECT_VERSION})
    set_target_properties(${_target_lib} PROPERTIES POSITION_INDEPENDENT_CODE 1)

    if (WIN32)
        list(APPEND LIBRARIES odbccp32 shlwapi)

        remove_definitions(-DUNICODE=1)

        if (MSVC_VERSION GREATER_EQUAL 1900)
            list(APPEND LIBRARIES legacy_stdio_definitions)
        endif()
    elseif(NOT APPLE)
        list(APPEND LIBRARIES odbcinst)
    endif()

    target_include_directories(${_target_lib} SYSTEM INTERFACE ${ODBC_INCLUDE_DIRS})
    target_link_libraries(${_target_lib} ${LIBRARIES})
endforeach()
unset(_target_libs)

if (${INSTALL_IGNITE_FILES})
    install(TARGETS ${TARGET}
        RUNTIME DESTINATION bin
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
    )
endif()

ignite_test(connection_info_test DISCOVER SOURCES config/connection_info_test.cpp LIBS ${TARGET}-obj ${LIBRARIES})
ignite_test(config_tools_test DISCOVER SOURCES config/config_tools_test.cpp LIBS ${TARGET}-obj ${LIBRARIES})
ignite_test(application_data_buffer_test DISCOVER SOURCES app/application_data_buffer_test.cpp LIBS ${TARGET}-obj ${LIBRARIES})

