/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/common/bytes_view.h>

#include <limits>

namespace ignite::protocol {

/**
 * Buffer adapter.
 *
 * Used to allow msgpack classes to write data to std::vector<std::byte>.
 */
class buffer_adapter {
public:
    /** Length header size in bytes. */
    static constexpr size_t LENGTH_HEADER_SIZE = 4;

    /**
     * Constructor.
     *
     * @param data Data.
     */
    explicit buffer_adapter(std::vector<std::byte> &data)
        : m_buffer(data)
        , m_length_pos(std::numeric_limits<std::size_t>::max()) {}

    /**
     * Write raw data.
     *
     * @param data Data to write.
     */
    void write_raw(bytes_view data) { m_buffer.insert(m_buffer.end(), data.begin(), data.end()); }

    /**
     * Get underlying data buffer view.
     *
     * @return Underlying data buffer view.
     */
    [[nodiscard]] bytes_view data() const { return m_buffer; }

    /**
     * Reserving space for length header.
     */
    void reserve_length_header() {
        m_length_pos = m_buffer.size();
        m_buffer.insert(m_buffer.end(), LENGTH_HEADER_SIZE, std::byte{0});
    }

    /**
     * Write buffer length to previously reserved position.
     */
    void write_length_header();

private:
    /** Buffer */
    std::vector<std::byte> &m_buffer;

    /** Length position. */
    std::size_t m_length_pos{std::numeric_limits<std::size_t>::max()};
};

} // namespace ignite::protocol
