#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

project(ignite-protocol)

set(TARGET ${PROJECT_NAME})

set(SOURCES
    sql/column_meta.cpp sql/column_meta.h
    bitset_span.h
    buffer_adapter.cpp buffer_adapter.h
    extension_types.h
    heartbeat_timeout.h
    messages.cpp messages.h
    partition_assignment.h
    protocol_context.h
    protocol_version.cpp protocol_version.h
    reader.cpp reader.h
    utils.cpp utils.h
    writer.cpp writer.h
)

add_library(${TARGET} OBJECT ${SOURCES})
target_link_libraries(${TARGET} ignite-common msgpack-c)

set_target_properties(${TARGET} PROPERTIES VERSION ${CMAKE_PROJECT_VERSION})
set_target_properties(${TARGET} PROPERTIES POSITION_INDEPENDENT_CODE 1)
