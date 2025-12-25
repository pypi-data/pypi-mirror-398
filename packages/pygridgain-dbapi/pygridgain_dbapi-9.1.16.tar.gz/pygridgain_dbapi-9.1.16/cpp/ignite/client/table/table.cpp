/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/table/table.h"
#include "ignite/client/detail/table/table_impl.h"

namespace ignite {

const std::string &table::get_name() const noexcept {
    return m_impl->get_name();
}

const qualified_name &table::get_qualified_name() const noexcept {
    return m_impl->get_qualified_name();
}

record_view<ignite_tuple> table::get_record_binary_view() const noexcept {
    return record_view<ignite_tuple>{m_impl};
}

key_value_view<ignite_tuple, ignite_tuple> table::get_key_value_binary_view() const noexcept {
    return key_value_view<ignite_tuple, ignite_tuple>{m_impl};
}

} // namespace ignite
