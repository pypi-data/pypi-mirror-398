/*
 * Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */


#pragma once

#include "ignite/common/end_point.h"

#include <vector>

#include <Python.h>

#include "ssl_config.h"


/**
 * Create a new instance of py_connection python class.
 *
 * @param addresses Addresses.
 * @param schema Schema.
 * @param identity Identity.
 * @param secret Secret.
 * @param page_size Page size.
 * @param timeout Timeout.
 * @param autocommit Autocommit flag.
 * @param ssl_cfg SSL Config.
 * @return A new connection class instance.
 */
PyObject* make_py_connection(std::vector<ignite::end_point> addresses, const char* schema, const char* identity,
    const char* secret, int page_size, int timeout, bool autocommit, ssl_config &&ssl_cfg);

/**
 * Prepare PyConnection type for registration.
 */
int prepare_py_connection_type();

/**
 * Register PyConnection type within module.
 */
int register_py_connection_type(PyObject* mod);