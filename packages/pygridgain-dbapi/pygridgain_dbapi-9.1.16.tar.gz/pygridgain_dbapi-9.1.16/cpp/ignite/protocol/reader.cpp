/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/protocol/reader.h"

#include <ignite/protocol/utils.h>

namespace ignite::protocol {

reader::reader(bytes_view buffer)
    : m_buffer(buffer)
    , m_current_val()
    , m_move_res(MSGPACK_UNPACK_SUCCESS) {

    msgpack_unpacked_init(&m_current_val);

    next();
}

bool reader::try_read_nil() {
    if (m_current_val.data.type != MSGPACK_OBJECT_NIL)
        return false;

    next();
    return true;
}

void reader::next() {
    check_data_in_stream();

    m_offset = m_offset_next;
    m_move_res = msgpack_unpack_next(
        &m_current_val, reinterpret_cast<const char *>(m_buffer.data()), m_buffer.size(), &m_offset_next);
}

} // namespace ignite::protocol
