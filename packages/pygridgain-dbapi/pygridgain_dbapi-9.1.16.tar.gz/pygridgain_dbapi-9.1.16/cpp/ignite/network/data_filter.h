/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/network/async_handler.h>
#include <ignite/network/data_sink.h>

#include <memory>
#include <vector>

namespace ignite::network {

/**
 * Data buffer.
 */
class data_filter : public data_sink, public async_handler {
public:
    /**
     * Set sink.
     *
     * @param sink Data sink
     */
    void set_sink(data_sink *sink) { m_sink = sink; }

    /**
     * Get sink.
     *
     * @return Data sink.
     */
    data_sink *get_sink() { return m_sink; }

    /**
     * Set handler.
     *
     * @param handler Event handler.
     */
    void set_handler(std::weak_ptr<async_handler> handler) { m_handler = std::move(handler); }

    /**
     * Get handler.
     *
     * @return Event handler.
     */
    std::shared_ptr<async_handler> get_handler() { return m_handler.lock(); }

protected:
    /** Sink. */
    data_sink *m_sink{nullptr};

    /** Handler. */
    std::weak_ptr<async_handler> m_handler{};
};

typedef std::vector<std::shared_ptr<data_filter>> data_filters;

} // namespace ignite::network
