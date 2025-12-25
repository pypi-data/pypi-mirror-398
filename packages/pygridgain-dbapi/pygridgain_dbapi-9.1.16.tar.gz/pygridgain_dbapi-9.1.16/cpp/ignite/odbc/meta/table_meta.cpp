/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/odbc/meta/table_meta.h"

namespace ignite {

void table_meta::read(protocol::reader &reader) {
    auto status = reader.read_int32();
    assert(status == 0);

    auto err_msg = reader.read_string_nullable();
    assert(!err_msg);

    schema_name = reader.read_string();
    table_name = reader.read_string();
    table_type = reader.read_string();
}

table_meta_vector read_table_meta_vector(protocol::reader &reader) {
    auto meta_num = reader.read_int32();

    table_meta_vector meta;
    meta.reserve(static_cast<std::size_t>(meta_num));

    for (std::int32_t i = 0; i < meta_num; ++i) {
        meta.emplace_back();
        meta.back().read(reader);
    }

    return meta;
}

} // namespace ignite
