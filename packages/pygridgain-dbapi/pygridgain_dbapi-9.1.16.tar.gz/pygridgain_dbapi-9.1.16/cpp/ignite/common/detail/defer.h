/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/common/ignite_error.h>

#include <memory>
#include <functional>

namespace ignite::detail {

/**
 * Deferred call, to be called when the scope is left.
 * Useful for cleanup routines.
 */
class deferred_call
{
public:
    /**
     * Constructor.
     *
     * @param val Instance, to call method on.
     * @param method Method to call.
     */
    explicit deferred_call(std::function<void()> routine) : m_routine(std::move(routine)) { }

    /**
     * Destructor.
     */
    ~deferred_call()
    {
        if (m_routine)
            m_routine();
    }

    /**
     * Release the deferred_call instance, without calling the stored function.
     */
    void release()
    {
        m_routine = {};
    }

private:
    /** Function to call. */
    std::function<void()> m_routine;
};

/**
 * Factory to construct a deferred call.
 *
 * @param routine Function to defer.
 * @return A new instance of the deferred call.
 */
inline deferred_call defer(std::function<void()> routine) {
    return deferred_call(std::move(routine));
}

} // namespace ignite::detail
