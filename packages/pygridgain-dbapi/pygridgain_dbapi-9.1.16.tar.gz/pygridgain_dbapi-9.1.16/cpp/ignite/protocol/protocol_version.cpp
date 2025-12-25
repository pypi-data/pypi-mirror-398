/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/protocol/protocol_version.h"
#include "ignite/common/ignite_error.h"

#include <sstream>

namespace ignite::protocol {

const protocol_version protocol_version::VERSION_3_0_0{3, 0, 0};

void throw_parse_error() {
    throw ignite_error(error::code::ILLEGAL_ARGUMENT,
        "Invalid version format. Valid format is X.Y.Z, where X, Y and Z are major, minor and maintenance "
        "version parts of Ignite since which protocol is introduced.");
}

std::optional<protocol_version> protocol_version::from_string(const std::string &version) {
    protocol_version res;

    std::stringstream buf(version);

    buf >> res.m_major;

    if (!buf.good())
        throw_parse_error();

    if (buf.get() != '.' || !buf.good())
        throw_parse_error();

    buf >> res.m_minor;

    if (!buf.good())
        throw_parse_error();

    if (buf.get() != '.' || !buf.good())
        throw_parse_error();

    buf >> res.m_patch;

    if (buf.bad())
        throw_parse_error();

    return res;
}

std::string protocol_version::to_string() const {
    std::stringstream buf;
    buf << m_major << '.' << m_minor << '.' << m_patch;

    return buf.str();
}

int32_t protocol_version::compare(const protocol_version &other) const {
    int32_t res = m_major - other.m_major;

    if (res == 0)
        res = m_minor - other.m_minor;

    if (res == 0)
        res = m_patch - other.m_patch;

    return res;
}

} // namespace ignite::protocol
