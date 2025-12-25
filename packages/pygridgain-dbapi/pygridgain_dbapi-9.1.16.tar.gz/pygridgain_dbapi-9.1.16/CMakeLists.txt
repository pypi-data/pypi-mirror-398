#
# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
#

cmake_minimum_required(VERSION 3.18)
project(pygridgain_dbapi VERSION ${IGNITE_VERSION} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Dealing with Python native libraries
set(Python_FIND_VIRTUALENV FIRST)
find_package(Python3 COMPONENTS Interpreter Development)

message("Python3_FOUND:${Python3_FOUND}")
message("Python3_VERSION:${Python3_VERSION}")
message("Python3_Development_FOUND:${Python3_Development_FOUND}")
message("Python3_LIBRARIES:${Python3_LIBRARIES}")
message("EXTENSION_FILENAME:${EXTENSION_FILENAME}")

# Dealing with Ignite C++ libraries
set(ENABLE_PROTOCOL ON)
set(ENABLE_NETWORK ON)
set(ENABLE_ODBC OFF)
set(ENABLE_CLIENT OFF)
set(ENABLE_TESTS OFF)
set(INSTALL_IGNITE_FILES OFF)
set(ENABLE_ADDRESS_SANITIZER OFF)
set(ENABLE_UB_SANITIZER OFF)
set(WARNINGS_AS_ERRORS OFF)
set(BUILD_SHARED_LIBS OFF)

if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/../../cpp)
    set(IGNITE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../cpp)
else()
    set(IGNITE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cpp)
endif()

set(IGNITE_BIN_DIR ${CMAKE_CURRENT_BINARY_DIR})
set(IGNITE_CMAKE_MODULE_PATH ${IGNITE_DIR}/cmake)

list(APPEND CMAKE_MODULE_PATH ${IGNITE_CMAKE_MODULE_PATH})
list(APPEND CMAKE_MODULE_PATH ${CMAKE_BINARY_DIR})
list(APPEND CMAKE_PREFIX_PATH ${CMAKE_BINARY_DIR})

include_directories(${IGNITE_DIR})

add_subdirectory(${IGNITE_DIR} ${IGNITE_BIN_DIR}/ignite)
add_subdirectory(cpp_module)
