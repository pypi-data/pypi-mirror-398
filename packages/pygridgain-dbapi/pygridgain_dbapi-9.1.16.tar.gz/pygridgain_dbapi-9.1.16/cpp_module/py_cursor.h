/*
 * Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */


#pragma once

#include <memory>

#include <Python.h>

#define PY_CURSOR_CLASS_NAME "PyCursor"

class statement;

/**
 * Cursor Python object.
 */
struct py_cursor {
    PyObject_HEAD

    /** Statement. */
    statement *m_statement;
};

/**
 * Create a new instance of py_cursor python class.
 *
 * @param stmt Statement.
 * @return A new class instance.
 */
py_cursor* make_py_cursor(std::unique_ptr<statement> stmt);

/**
 * Prepare PyCursor type for registration.
 */
int prepare_py_cursor_type();

/**
 * Register PyCursor type within module.
 */
int register_py_cursor_type(PyObject* mod);
