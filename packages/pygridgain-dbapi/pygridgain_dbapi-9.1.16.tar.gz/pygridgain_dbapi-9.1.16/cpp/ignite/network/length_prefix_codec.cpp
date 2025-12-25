/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "length_prefix_codec.h"

#include "ignite/common/detail/bytes.h"
#include <ignite/protocol/utils.h>

namespace ignite::network {

length_prefix_codec::length_prefix_codec()
    : m_packet_size(-1)
    , m_packet()
    , m_magic_received(false) {
}

data_buffer_owning length_prefix_codec::encode(data_buffer_owning &data) {
    // Just pass data as is, because we encode message size in
    // the application to avoid unnecessary re-allocations and copying.
    return data.consume_entirely();
}

void length_prefix_codec::reset_buffer() {
    m_packet_size = -1;
    m_packet.clear();
}

data_buffer_ref length_prefix_codec::decode(data_buffer_ref &data) {
    if (!m_magic_received) {
        consume(data, int32_t(protocol::MAGIC_BYTES.size()));

        if (m_packet.size() < protocol::MAGIC_BYTES.size())
            return {};

        if (!std::equal(protocol::MAGIC_BYTES.begin(), protocol::MAGIC_BYTES.end(), m_packet.begin(), m_packet.end()))
            throw ignite_error(error::code::PROTOCOL, "Unknown protocol is used by the server (wrong port?)");

        reset_buffer();
        m_magic_received = true;
    }

    if (m_packet.empty() || m_packet.size() == (PACKET_HEADER_SIZE + m_packet_size))
        reset_buffer();

    if (m_packet_size < 0) {
        consume(data, PACKET_HEADER_SIZE);

        if (m_packet.size() < PACKET_HEADER_SIZE)
            return {};

        m_packet_size = detail::bytes::load<detail::endian::BIG, int32_t>(m_packet.data());
    }

    consume(data, m_packet_size + PACKET_HEADER_SIZE);

    if (m_packet.size() == m_packet_size + PACKET_HEADER_SIZE)
        return {m_packet, PACKET_HEADER_SIZE, m_packet_size + PACKET_HEADER_SIZE};

    return {};
}

void length_prefix_codec::consume(data_buffer_ref &data, size_t desired) {
    auto to_copy = desired - m_packet.size();
    if (to_copy <= 0)
        return;

    data.consume_by(m_packet, size_t(to_copy));
}

} // namespace ignite::network
