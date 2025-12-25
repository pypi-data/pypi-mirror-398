/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/network/data_filter_adapter.h>
#include <ignite/network/ssl/secure_configuration.h>

#include <map>
#include <memory>
#include <mutex>

namespace ignite::network
{

/**
 * TLS/SSL Data Filter.
 */
class secure_data_filter : public data_filter_adapter
{
public:
    /**
     * Constructor.
     *
     * @param cfg Configuration.
     */
    explicit secure_data_filter(const secure_configuration &cfg);

    /**
     * Destructor.
     */
    ~secure_data_filter() override;

    /**
     * Send data to specific established connection.
     *
     * @param id Client ID.
     * @param data Data to be sent.
     * @return @c true if connection is present and @c false otherwise.
     *
     * @throw ignite_error on error.
     */
    bool send(std::uint64_t id, std::vector<std::byte> &&data) override;

    /**
      * Callback that called on successful connection establishment.
      *
      * @param addr Address of the new connection.
      * @param id Connection ID.
      */
    void on_connection_success(const end_point& addr, std::uint64_t id) override;

    /**
     * Callback that called on error during connection establishment.
     *
     * @param id Async client ID.
     * @param err Error. Can be null if connection closed without error.
     */
    void on_connection_closed(std::uint64_t id, std::optional<ignite_error> err) override;

    /**
     * Callback that called when new message is received.
     *
     * @param id Async client ID.
     * @param msg Received message.
     */
    void on_message_received(std::uint64_t id, bytes_view msg) override;

private:
    /**
     * Secure connection context.
     */
    class secure_connection_context
    {
    public:
        /**
         * Default constructor.
         *
         * @param id Connection ID.
         * @param addr Address.
         * @param filter Filter.
         */
        secure_connection_context(std::uint64_t id, end_point addr, secure_data_filter &filter);

        /**
         * Destructor.
         */
        ~secure_connection_context();

        /**
         * Start connection procedure including handshake.
         *
         * @return @c true, if connection complete.
         */
        bool do_connect();

        /**
         * Check whether connection is established.
         *
         * @return @c true if connection established.
         */
        [[nodiscard]] bool is_connected() const { return m_connected; }

        /**
         * Get address.
         *
         * @return Address.
         */
        [[nodiscard]] const end_point& get_address() const { return m_addr; }

        /**
         * Send data.
         *
         * @param data Data to send.
         * @return @c true on success.
         */
        bool send(const std::vector<std::byte> &data);

        /**
         * Process new data.
         *
         * @param data Data received.
         * @return @c true if connection was established.
         */
        bool process_data(data_buffer_ref &data);

        /**
         * Get pending decrypted data.
         *
         * @return Data buffer.
         */
        data_buffer_ref get_pending_decrypted_data();

    private:
        enum
        {
            /** Receive buffer size. */
            DEFAULT_BUFFER_SIZE = 0x10000
        };

        /**
         * Send pending data.
         */
        bool send_pending_data();

        /**
         * Get pending data.
         *
         * @param bio BIO to get data from.
         * @return Data buffer.
         */
        static std::vector<std::byte> get_pending_data(void* bio);

        /** Flag indicating that secure connection is established. */
        bool m_connected{false};

        /** Connection ID. */
        const std::uint64_t m_id;

        /** Address. */
        const end_point m_addr;

        /** Filter. */
        secure_data_filter &m_filter;

        /** Receive buffer. */
        std::vector<std::byte> m_recv_buffer{DEFAULT_BUFFER_SIZE, {}};

        /** SSL instance. */
        void* m_ssl{nullptr};

        /** Input BIO. */
        void* m_bio_in{nullptr};

        /** Output BIO. */
        void* m_bio_out{nullptr};
    };

    /** Context map. */
    typedef std::map<std::uint64_t, std::shared_ptr<secure_connection_context>> context_map;

    /**
     * Get context for connection.
     *
     * @param id Connection ID.
     * @return Context if found or null.
     */
    std::shared_ptr<secure_connection_context> find_context(std::uint64_t id);

    /**
     * Send data to specific established connection.
     *
     * @param id Client ID.
     * @param data Data to be sent.
     * @return @c true if connection is present and @c false otherwise.
     *
     * @throw ignite_error on error.
     */
    bool send_internal(std::uint64_t id, std::vector<std::byte> data);

    /** SSL context. */
    void* m_ssl_context{nullptr};

    /** Contexts for connections. */
    context_map m_contexts;

    /** Mutex for secure access to context map. */
    std::mutex m_context_mutex;
};

}
