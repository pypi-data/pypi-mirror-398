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
#include <ignite/network/data_buffer.h>

namespace ignite::network {

/**
 * Data sink. Can consume data.
 */
class data_sink {
public:
    // Default.
    virtual ~data_sink() = default;

    /**
     * Send data to specific established connection.
     *
     * @param id Client ID.
     * @param data Data to be sent.
     * @return @c true if connection is present and @c false otherwise.
     *
     * @throw ignite_error on error.
     */
    virtual bool send(uint64_t id, std::vector<std::byte> &&data) = 0;

    /**
     * Closes specified connection if it's established. Connection to the specified address is planned for
     * re-connect. Error is reported to handler.
     *
     * @param id Client ID.
     * @param err Optional error.
     */
    virtual void close(uint64_t id, std::optional<ignite_error> err) = 0;
};

} // namespace ignite::network
