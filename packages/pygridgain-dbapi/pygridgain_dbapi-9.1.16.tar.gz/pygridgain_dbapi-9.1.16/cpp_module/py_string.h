/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "py_object.h"

#include <string>

#include <Python.h>

class py_string : public py_object_based {
public:
    // Default
    py_string() = default;

    /**
     * Make a string from python object.
     *
     * @param obj Python Object.
     * @return A new instance of the class. Can be invalid if the object was not a valid utf-8 string.
     *
     * @warning Error is set if an invalid object is returned.
     */
    static py_string try_from_py_utf8(PyObject* obj) {
        py_object val{PyUnicode_AsUTF8String(obj)};
        if (!val)
            return {};

        return py_string{std::move(val)};
    }

    /**
     * Get string data.
     *
     * @return String data.
     */
    std::string_view get_data() const { return m_data; }

    /**
     * Get string data.
     *
     * @return String data.
     */
    std::string_view operator*() const { return get_data(); }

private:
    /**
     * Constructor.
     *
     * @param obj Object.
     */
    explicit py_string(py_object &&obj)
        : py_object_based(std::move(obj))
        , m_data(PyBytes_AsString(m_obj.get()), PyBytes_Size(m_obj.get())) {}

    /** The actual string data. */
    std::string_view m_data;
};
