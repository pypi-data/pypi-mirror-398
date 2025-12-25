#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

project(ignite-common)

set(TARGET ${PROJECT_NAME})

set(PUBLIC_HEADERS
    big_decimal.h
    big_integer.h
    binary_object.h
    bytes_view.h
    detail/bits.h
    detail/byte_traits.h
    detail/bytes.h
    detail/config.h
    detail/mpi.h
    end_point.h
    error_codes.h
    ignite_date.h
    ignite_date_time.h
    ignite_duration.h
    ignite_error.h
    ignite_period.h
    ignite_result.h
    ignite_time.h
    ignite_timestamp.h
    ignite_type.h
    primitive.h
    uuid.h
)

set(SOURCES
    big_decimal.cpp
    big_integer.cpp
    detail/hash_utils.cpp
    detail/name_utils.cpp
    detail/mpi.cpp
    detail/string_utils.cpp
    detail/thread_timer.cpp
    uuid.cpp
)

add_library(${TARGET} STATIC ${SOURCES})

target_link_libraries(${TARGET} PUBLIC
    MbedTLS::mbedtls
    uni-algo::uni-algo
)

target_include_directories(${TARGET} INTERFACE
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}>
    $<INSTALL_INTERFACE:${IGNITE_INCLUDEDIR}>
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

if (${INSTALL_IGNITE_FILES})
    ignite_install_headers(FILES ${PUBLIC_HEADERS} DESTINATION ${IGNITE_INCLUDEDIR}/common)
endif()

ignite_test(bits_test DISCOVER SOURCES detail/bits_test.cpp LIBS ${TARGET})
ignite_test(bytes_test DISCOVER SOURCES detail/bytes_test.cpp LIBS ${TARGET})
ignite_test(string_utils_test DISCOVER SOURCES detail/string_utils_test.cpp LIBS ${TARGET})
ignite_test(thread_timer_test DISCOVER SOURCES detail/thread_timer_test.cpp LIBS ${TARGET})
ignite_test(uuid_test DISCOVER SOURCES uuid_test.cpp LIBS ${TARGET})
ignite_test(bignum_test DISCOVER SOURCES bignum_test.cpp LIBS ${TARGET})
ignite_test(primitive_test DISCOVER SOURCES primitive_test.cpp LIBS ${TARGET})
ignite_test(name_utils_test DISCOVER SOURCES detail/name_utils_test.cpp LIBS ${TARGET})
ignite_test(hash_utils_test DISCOVER SOURCES detail/hash_utils_test.cpp LIBS ${TARGET})
