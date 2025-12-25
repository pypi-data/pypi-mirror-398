/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

/**
 * @file
 * Declares ignite::cancellation_token.
 */

#pragma once

namespace ignite
{

/**
 * @brief Execution cancellation token.
 *
 * Cancellation token is an object that is issued by @ref ignite::cancel_handle and can be used by an operation
 * or a resource to observe a signal to terminate it.
 */
class cancellation_token
{
public:
    /** Destructor. */
    virtual ~cancellation_token() = default;
};

} // namespace ignite
