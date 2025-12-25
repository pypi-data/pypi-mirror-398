/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/protocol/protocol_context.h"
#include "ignite/protocol/protocol_version.h"
#include "ignite/protocol/writer.h"
#include "ignite/protocol/reader.h"
#include "ignite/protocol/partition_assignment.h"

#include "ignite/common/bytes_view.h"
#include "ignite/common/ignite_error.h"

#include <map>
#include <vector>


namespace ignite::protocol {

constexpr std::size_t HEADER_SIZE = 4;

/**
 * Response flags.
 */
enum class response_flag : std::int32_t {
    /// Partition assignment changed in cluster.s
    PARTITION_ASSIGNMENT_CHANGED = 1,

    /// Notification flag.
    NOTIFICATION_FLAG = 2,

    /// Error flag.
    ERROR_FLAG = 4,
};

/**
 * Test whether the flag is set.
 *
 * @param flags Flags.
 * @param to_test A specific flag to test.
 * @return @c true if the flag is set.
 */
inline bool test_flag(std::int32_t flags, response_flag to_test) {
    return (flags & std::int32_t(to_test)) != 0;
}

/**
 * Handshake response.
 */
struct handshake_response {
    /** Error. */
    std::optional<ignite_error> error{};

    /** Protocol context. */
    protocol_context context{};

    /** Observable timestamp. */
    std::int64_t observable_timestamp;

    /** Server idle timeout in ms. */
    std::int64_t idle_timeout_ms;

    /** Node name. */
    std::string node_name;
};

/**
 * Make handshake request.
 *
 * @param client_type Client type.
 * @param ver Protocol version.
 * @param extensions Extensions.
 * @return Message.
 */
std::vector<std::byte> make_handshake_request(
    std::int8_t client_type, protocol_version ver, std::map<std::string, std::string> extensions);

/**
 * Parse handshake response.
 *
 * @param message Message to parse.
 * @return Handshake response.
 */
handshake_response parse_handshake_response(bytes_view message);

/**
 * Write partition assignment request.
 *
 * @param writer Writer.
 * @param table_id Table ID.
 * @param timestamp Timestamp.
 */
void write_partition_assignment_request(writer &writer, std::int32_t table_id, std::int64_t timestamp);

/**
 * Read assignment response.
 *
 * @param reader Reader.
 * @param timestamp Timestamp.
 * @return A new assignment.
 */
std::shared_ptr<partition_assignment> read_partition_assignment_response(reader &reader, std::int64_t timestamp);

} // namespace ignite::protocol
