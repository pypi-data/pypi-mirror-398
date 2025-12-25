/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <Python.h>

/**
 * Safer wrapper of PyObject.
 */
class py_object {
public:
    // Default
    py_object() = default;

    // Delete.
    py_object(const py_object&) = delete;
    py_object& operator=(const py_object&) = delete;

    /**
     * Move constructor.
     *
     * @param another Another Object.
     */
    py_object(py_object&& another) noexcept
        : m_obj(another.m_obj) {
        another.m_obj = nullptr;
    }

    /**
     * Move operator.
     *
     * @param another Another Object.
     * @return This.
     */
    py_object& operator=(py_object&& another) noexcept {
        std::swap(m_obj, another.m_obj);
        another.reset();

        return *this;
    }

    /**
     * Basic constructor.
     *
     * @param obj Python Object.
     */
    py_object(PyObject* obj) : m_obj(obj) {}

    /**
     * Destructor.
     */
    ~py_object() {
        reset();
    }

    /**
     * Check whether the object is valid.
     */
    bool is_valid() const { return m_obj != nullptr; }

    /**
     * Check whether the object is valid.
     */
    operator bool() const { return is_valid(); }

    /**
     * Change the value of the python object.
     *
     * @param obj New value.
     */
    void reset(PyObject* obj = nullptr) {
        Py_XDECREF(m_obj);
        m_obj = obj;
    }

    /**
     * Get Pointer.
     */
    PyObject* get() { return m_obj; }

    /**
     * Get Pointer.
     */
    const PyObject* get() const { return m_obj; }

private:
    /** Reference to the python object. */
    PyObject* m_obj{nullptr};
};

/**
 * Class to be used to inherit the basic and safe behavior of py_object.
 */
class py_object_based {
public:
    py_object_based() = default;

    /**
     * Check whether the object is valid.
     */
    bool is_valid() const { return m_obj.is_valid(); }

    /**
     * Check whether the object is valid.
     */
    operator bool() const { return is_valid(); }

protected:
    /**
     * Constructor.
     *
     * @param obj Object.
     */
    explicit py_object_based(py_object &&obj) : m_obj(std::move(obj)) {}

    /** Object. */
    py_object m_obj{};
};

