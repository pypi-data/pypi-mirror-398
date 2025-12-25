#
# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
#

project(_pygridgain_dbapi_extension)

set(TARGET ${PROJECT_NAME})

set(SOURCES
    module.cpp
    py_connection.cpp
    py_cursor.cpp
    statement.cpp
    utils.cpp
)

set(LIBRARIES
    ignite-common
    ignite-tuple
    ignite-network
    ignite-protocol
)

if(APPLE)
    add_link_options(-undefined dynamic_lookup)
endif()

add_library(${TARGET} SHARED ${SOURCES})

target_include_directories(${TARGET} PUBLIC
    ${Python3_INCLUDE_DIRS}
)

if(NOT DEFINED EXTENSION_FILENAME)
    set(EXTENSION_FILENAME ${TARGET})
endif()

target_link_libraries(${TARGET} ${LIBRARIES})
set_target_properties(${TARGET} PROPERTIES OUTPUT_NAME ${EXTENSION_FILENAME})

if (WIN32)
    add_compile_definitions(NOMINMAX)
    set_target_properties(${TARGET} PROPERTIES SUFFIX ".pyd")
    target_link_libraries(${TARGET} ${Python3_LIBRARIES})
    remove_definitions(-DUNICODE=1)
elseif(APPLE)
    set_target_properties(${TARGET} PROPERTIES
        PREFIX ""
        SUFFIX ".so"
    )
else()
    set_target_properties(${TARGET} PROPERTIES PREFIX "")
endif()

