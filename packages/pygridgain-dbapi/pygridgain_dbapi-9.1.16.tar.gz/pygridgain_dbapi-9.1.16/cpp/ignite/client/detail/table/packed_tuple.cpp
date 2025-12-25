/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include <ignite/client/detail/table/packed_tuple.h>
#include <ignite/client/detail/utils.h>

namespace ignite::detail {

ignite_tuple packed_tuple::unpack(bool key_only) const {
    return decode_tuple(m_data, m_schema.get(), key_only);
}

ignite_tuple packed_tuple::unpack_key() const {
    return decode_tuple_key(m_data, m_schema.get());
}

ignite_tuple packed_tuple::unpack_value() const {
    return decode_tuple_value(m_data, m_schema.get());
}

} // namespace ignite::detail
