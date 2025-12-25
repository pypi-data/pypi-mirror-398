/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/network/detail/win/sockets.h"

#include "ignite/common/ignite_error.h"

#include <cstdint>
#include <thread>

namespace ignite::network::detail {

/** Windows async client pool. */
class win_async_client_pool;

/**
 * Async pool worker thread.
 */
class win_async_worker_thread {
public:
    /**
     * Constructor.
     */
    win_async_worker_thread();

    /**
     * Start thread.
     *
     * @param clientPool Client pool.
     * @param iocp Valid IOCP instance handle.
     */
    void start(win_async_client_pool &clientPool, HANDLE iocp);

    /**
     * Stop thread.
     */
    void stop();

private:
    /**
     * Run thread.
     */
    void run();

    /** Thread. */
    std::thread m_thread;

    /** Flag to signal that thread should stop. */
    volatile bool m_stopping;

    /** Client pool. */
    win_async_client_pool *m_client_pool;

    /** IO Completion Port. Windows-specific primitive for asynchronous IO. */
    HANDLE m_iocp;
};

} // namespace ignite::network::detail
