/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/network/codec.h>
#include <ignite/network/data_filter_adapter.h>

#include <map>
#include <mutex>
#include <optional>

namespace ignite::network {

/**
 * Data filter that uses codecs inside to encode/decode data.
 */
class codec_data_filter : public data_filter_adapter {
public:
    /**
     * Constructor.
     *
     * @param factory Codec factory.
     */
    explicit codec_data_filter(std::shared_ptr<detail::factory<codec>> factory);

    /**
     * Send data to specific established connection.
     *
     * @param id Client ID.
     * @param data Data to be sent.
     * @return @c true if connection is present and @c false otherwise.
     *
     * @throw ignite_error on error.
     */
    bool send(uint64_t id, std::vector<std::byte> &&data) override;

    /**
     * Callback that called on successful connection establishment.
     *
     * @param addr Address of the new connection.
     * @param id Connection ID.
     */
    void on_connection_success(const end_point &addr, uint64_t id) override;

    /**
     * Callback that called on error during connection establishment.
     *
     * @param id Async client ID.
     * @param err Error. Can be null if connection closed without error.
     */
    void on_connection_closed(uint64_t id, std::optional<ignite_error> err) override;

    /**
     * Callback that called when new message is received.
     *
     * @param id Async client ID.
     * @param msg Received message.
     */
    void on_message_received(uint64_t id, bytes_view msg) override;

private:
    /**
     * Get codec for connection.
     *
     * @param id Connection ID.
     * @return Codec if found or null.
     */
    std::shared_ptr<codec> find_codec(uint64_t id);

    /** Codec factory. */
    std::shared_ptr<detail::factory<codec>> m_codec_factory;

    /** Codecs. */
    std::map<uint64_t, std::shared_ptr<codec>> m_codecs;

    /** Mutex for secure access to codecs map. */
    std::mutex m_codecs_mutex;
};

} // namespace ignite::network
