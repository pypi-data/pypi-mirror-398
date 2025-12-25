/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/protocol/buffer_adapter.h"

#include "ignite/common/detail/bytes.h"
#include <ignite/common/ignite_error.h>
#include <ignite/protocol/utils.h>

namespace ignite::protocol {

void buffer_adapter::write_length_header() {
    if (m_length_pos == std::numeric_limits<std::size_t>::max() || m_length_pos + LENGTH_HEADER_SIZE > m_buffer.size())
        throw ignite_error("Length header was not reserved properly in buffer");

    auto length = std::int32_t(m_buffer.size() - (m_length_pos + LENGTH_HEADER_SIZE));

    detail::bytes::store<detail::endian::BIG, int32_t>(m_buffer.data() + m_length_pos, length);
}

} // namespace ignite::protocol
