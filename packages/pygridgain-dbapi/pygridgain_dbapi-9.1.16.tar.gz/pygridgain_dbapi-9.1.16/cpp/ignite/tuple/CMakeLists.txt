#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

project(ignite-tuple)

set(TARGET ${PROJECT_NAME})

set(SOURCES
    binary_tuple_builder.cpp
    binary_tuple_parser.cpp
)

set(PUBLIC_HEADERS
    binary_tuple_builder.h
    binary_tuple_common.h
    binary_tuple_parser.h
)

add_library(${TARGET} STATIC ${SOURCES})

target_link_libraries(${TARGET} ignite-common)

ignite_test(tuple_test DISCOVER SOURCES tuple_test.cpp LIBS ${TARGET})

if (${INSTALL_IGNITE_FILES})
    install(TARGETS ${TARGET}
        RUNTIME DESTINATION bin
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
    )

    ignite_install_headers(FILES ${PUBLIC_HEADERS} DESTINATION ${IGNITE_INCLUDEDIR}/tuple)
endif()
