/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "connecting_context.h"

#include <cstring>
#include <iterator>

#include <netdb.h>
#include <sys/epoll.h>
#include <sys/socket.h>

namespace ignite::network::detail {

connecting_context::connecting_context(tcp_range range)
    : m_range(std::move(range))
    , m_next_port(range.port)
    , m_info(nullptr)
    , m_current_info(nullptr) {
}

connecting_context::~connecting_context() {
    reset();
}

void connecting_context::reset() {
    if (m_info) {
        freeaddrinfo(m_info);
        m_info = nullptr;
        m_current_info = nullptr;
    }

    m_next_port = m_range.port;
}

addrinfo *connecting_context::next() {
    if (m_current_info)
        m_current_info = m_current_info->ai_next;

    while (!m_current_info) {
        if (m_info) {
            freeaddrinfo(m_info);
            m_info = nullptr;
        }

        if (m_next_port > m_range.port + m_range.range)
            return nullptr;

        addrinfo hints{};
        std::memset(&hints, 0, sizeof(hints));

        hints.ai_family = AF_UNSPEC;
        hints.ai_socktype = SOCK_STREAM;
        hints.ai_protocol = IPPROTO_TCP;

        std::string strPort = std::to_string(m_next_port);

        // Resolve the server address and port
        int res = getaddrinfo(m_range.host.c_str(), strPort.c_str(), &hints, &m_info);
        if (res != 0)
            return nullptr;

        m_current_info = m_info;
        ++m_next_port;
    }

    return m_current_info;
}

end_point connecting_context::current_address() const {
    if (!m_current_info)
        throw ignite_error("There is no current address");

    return {m_range.host, uint16_t(m_next_port - 1)};
}

std::shared_ptr<linux_async_client> connecting_context::to_client(int fd) {
    return std::make_shared<linux_async_client>(fd, current_address(), m_range);
}

} // namespace ignite::network::detail
