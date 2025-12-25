/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/network/cluster_node.h"
#include "ignite/client/detail/table/schema.h"
#include "ignite/client/table/ignite_tuple.h"
#include "ignite/client/transaction/transaction.h"

#include "ignite/protocol/writer.h"

namespace ignite::detail {
struct schema;

/**
 * Tuple concatenation function.
 *
 * @param left Left-hand value.
 * @param right Right-hand value.
 * @return Resulting tuple.
 */
[[nodiscard]] ignite_tuple concat(const ignite_tuple &left, const ignite_tuple &right);

/**
 * Write tuple using table schema and writer.
 *
 * @param writer Writer.
 * @param sch Schema.
 * @param tuple Tuple.
 * @param key_only Indicates whether only key fields should be written or not.
 */
void write_tuple(protocol::writer &writer, const schema &sch, const ignite_tuple &tuple, bool key_only);

/**
 * Write tuples using table schema and writer.
 *
 * @param writer Writer.
 * @param sch Schema.
 * @param tuples Tuples.
 * @param key_only Indicates whether only key fields should be written or not.
 */
void write_tuples(protocol::writer &writer, const schema &sch, const std::vector<ignite_tuple> &tuples, bool key_only);

/**
 * Decode tuple from bytes.
 *
 * @param tuple_data Tuple data.
 * @param sch Schema.
 * @param key_only Should only key fields be read or not.
 * @return Tuple.
 */
ignite_tuple decode_tuple(bytes_view tuple_data, const schema *sch, bool key_only);

/**
 * Decode key part of the tuple from bytes.
 *
 * @param tuple_data Tuple data.
 * @param sch Schema.
 * @return Tuple.
 */
ignite_tuple decode_tuple_key(bytes_view tuple_data, const schema *sch);

/**
 * Decode value part of the tuple from bytes.
 *
 * @param tuple_data Tuple data.
 * @param sch Schema.
 * @return Tuple.
 */
ignite_tuple decode_tuple_value(bytes_view tuple_data, const schema *sch);

/**
 * Read tuple.
 *
 * @param reader Reader.
 * @param sch Schema.
 * @param key_only Indicates whether only key fields should be written or not.
 * @return Tuple.
 */
ignite_tuple read_tuple(protocol::reader &reader, const schema *sch, bool key_only);

/**
 * Read tuple.
 *
 * @param reader Reader.
 * @param sch Schema.
 * @return Tuple.
 */
std::optional<ignite_tuple> read_tuple_opt(protocol::reader &reader, const schema *sch);

/**
 * Read tuples.
 *
 * @param reader Reader.
 * @param sch Schema.
 * @param key_only Indicates whether only key fields should be written or not.
 * @return Tuples.
 */
std::vector<ignite_tuple> read_tuples(protocol::reader &reader, const schema *sch, bool key_only);

/**
 * Read tuples.
 *
 * @param reader Reader.
 * @param sch Schema.
 * @param key_only Indicates whether only key fields should be written or not.
 * @return Tuples.
 */
std::vector<std::optional<ignite_tuple>> read_tuples_opt(protocol::reader &reader, const schema *sch, bool key_only);

/**
 * Read cluster node.
 *
 * @param reader Reader.
 * @return Cluster node.
 */
cluster_node read_cluster_node(protocol::reader &reader);

} // namespace ignite::detail
