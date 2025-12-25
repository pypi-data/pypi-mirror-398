/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/protocol/writer.h"

namespace ignite::protocol {

int writer::write_callback(void *data, const char *buf, size_t len) {
    if (!data)
        return 0;

    auto buffer = static_cast<buffer_adapter *>(data);

    // We do not support messages larger than MAX_INT32
    if (buffer->data().size() + len > std::size_t(std::numeric_limits<int32_t>::max()))
        return -1;

    auto bytes = reinterpret_cast<const std::byte *>(buf);
    buffer->write_raw(bytes_view{bytes, len});

    return 0;
}

} // namespace ignite::protocol
