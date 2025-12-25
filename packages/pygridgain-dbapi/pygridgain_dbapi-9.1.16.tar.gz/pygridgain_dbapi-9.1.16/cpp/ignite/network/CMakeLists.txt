#  Copyright (C) GridGain Systems. All Rights Reserved.
#  _________        _____ __________________        _____
#  __  ____/___________(_)______  /__  ____/______ ____(_)_______
#  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
#  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
#  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/

project(ignite-network)

set(TARGET ${PROJECT_NAME})

find_package(OpenSSL)
if (EXISTS ${OPENSSL_INCLUDE_DIR})
    message(STATUS "OPENSSL_INCLUDE_DIR: " ${OPENSSL_INCLUDE_DIR})
else()
    message(FATAL_ERROR "Can not resolve OPENSSL_INCLUDE_DIR.")
endif()

set(SOURCES
    async_client_pool_adapter.cpp
    error_handling_filter.cpp
    codec_data_filter.cpp
    length_prefix_codec.cpp
    network.cpp
    tcp_range.cpp
    ssl/secure_data_filter.cpp
    ssl/secure_socket_client.cpp
    ssl/secure_utils.cpp
    ssl/ssl_gateway.cpp
)

if(WIN32)
    list(APPEND SOURCES
        detail/win/dynamic_module.cpp
        detail/win/sockets.cpp
        detail/win/utils.cpp
        detail/win/win_async_client.cpp
        detail/win/win_async_client_pool.cpp
        detail/win/win_async_connecting_thread.cpp
        detail/win/win_async_worker_thread.cpp
    )
elseif(APPLE)
    list(APPEND SOURCES
        detail/linux/connecting_context.cpp
        detail/linux/dynamic_module.cpp
        detail/macos/macos_async_client.cpp
        detail/linux/linux_async_client_pool.cpp
        detail/macos/macos_async_worker_thread.cpp
        detail/linux/sockets.cpp
        detail/linux/utils.cpp
    )
elseif(UNIX)
    list(APPEND SOURCES
        detail/linux/connecting_context.cpp
        detail/linux/dynamic_module.cpp
        detail/linux/linux_async_client.cpp
        detail/linux/linux_async_client_pool.cpp
        detail/linux/linux_async_worker_thread.cpp
        detail/linux/sockets.cpp
        detail/linux/utils.cpp
    )
endif()

add_library(${TARGET} OBJECT ${SOURCES})

target_link_libraries(${TARGET} PUBLIC ignite-common ignite-protocol)
target_include_directories(${TARGET} PRIVATE ${OPENSSL_INCLUDE_DIR})

if(WIN32)
    add_definitions(-D_WINSOCK_DEPRECATED_NO_WARNINGS)
    target_link_libraries(${TARGET} PUBLIC wsock32 ws2_32 iphlpapi crypt32)
elseif(APPLE)
    if (${USE_LOCAL_DEPS})
        find_package(epoll-shim REQUIRED)
        target_link_libraries(${TARGET} PUBLIC epoll-shim::epoll-shim ${CMAKE_DL_LIBS})
    else()
        fetch_dependency(epoll-shim https://github.com/jiixyj/epoll-shim/archive/refs/tags/v0.0.20240608.tar.gz 9751ab5cad7bff8a1388a951276247bf)
        target_link_libraries(${TARGET} PUBLIC epoll-shim)
    endif()
    add_compile_definitions(EPOLL_SHIM_NO_VARIADICS)
elseif(UNIX)
    target_link_libraries(${TARGET} PUBLIC ${CMAKE_DL_LIBS})
endif()

set_target_properties(${TARGET} PROPERTIES VERSION ${CMAKE_PROJECT_VERSION})
set_target_properties(${TARGET} PROPERTIES POSITION_INDEPENDENT_CODE 1)
