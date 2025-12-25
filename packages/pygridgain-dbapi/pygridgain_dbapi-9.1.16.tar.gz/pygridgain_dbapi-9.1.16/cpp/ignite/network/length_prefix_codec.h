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
#include <ignite/network/codec.h>

#include <cstddef>
#include <vector>

namespace ignite::network {

/**
 * Codec that decodes messages prefixed with int32 length.
 */
class length_prefix_codec : public codec {
public:
    /** Packet header size in bytes. */
    static constexpr size_t PACKET_HEADER_SIZE = 4;

    /**
     * Constructor.
     */
    length_prefix_codec();

    /**
     * Encode provided data.
     *
     * @param data Data to encode.
     * @return Encoded data. Returning null is ok.
     *
     * @throw ignite_error on error.
     */
    data_buffer_owning encode(data_buffer_owning &data) override;

    /**
     * Decode provided data.
     *
     * @param data Data to decode.
     * @return Decoded data. Returning null means data is not yet ready.
     *
     * @throw ignite_error on error.
     */
    data_buffer_ref decode(data_buffer_ref &data) override;

private:
    /**
     * Consume the right amount of provided data to make packet closer to desired size.
     *
     * @param data Data to consume.
     * @param desired Desired resulting size of packet.
     */
    void consume(data_buffer_ref &data, size_t desired);

    /**
     * reset packet buffer.
     */
    void reset_buffer();

    /** Size of the current packet. */
    int32_t m_packet_size;

    /** Current packet. */
    std::vector<std::byte> m_packet;

    /** Magic bytes received. */
    bool m_magic_received;
};

/** Factory for length_prefix_codec. */
typedef detail::basic_factory<codec, length_prefix_codec> length_prefix_codec_factory;

} // namespace ignite::network
