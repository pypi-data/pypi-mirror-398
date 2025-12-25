/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "async_client_pool_adapter.h"

#include "error_handling_filter.h"

namespace ignite::network {

async_client_pool_adapter::async_client_pool_adapter(data_filters filters, std::shared_ptr<async_client_pool> pool)
    : m_filters(std::move(filters))
    , m_pool(std::move(pool))
    , m_sink(m_pool.get()) {
    m_filters.insert(m_filters.begin(), std::make_shared<error_handling_filter>());

    for (const auto &filter : m_filters) {
        filter->set_sink(m_sink);
        m_sink = filter.get();
    }
}

void async_client_pool_adapter::start(std::vector<tcp_range> addrs, uint32_t connLimit) {
    m_pool->start(std::move(addrs), connLimit);
}

void async_client_pool_adapter::stop() {
    m_pool->stop();
}

void async_client_pool_adapter::set_handler(std::weak_ptr<async_handler> handler) {
    auto handler0 = std::move(handler);
    for (auto it = m_filters.rbegin(); it != m_filters.rend(); ++it) {
        (*it)->set_handler(std::move(handler0));
        handler0 = *it;
    }

    m_pool->set_handler(std::move(handler0));
}

bool async_client_pool_adapter::send(uint64_t id, std::vector<std::byte> &&data) {
    return m_sink->send(id, std::move(data));
}

void async_client_pool_adapter::close(uint64_t id, std::optional<ignite_error> err) {
    m_sink->close(id, std::move(err));
}

} // namespace ignite::network
