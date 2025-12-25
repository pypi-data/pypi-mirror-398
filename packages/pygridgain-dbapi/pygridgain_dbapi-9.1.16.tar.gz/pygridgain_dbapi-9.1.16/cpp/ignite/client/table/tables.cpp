/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/table/tables.h"
#include "ignite/client/detail/table/tables_impl.h"

namespace ignite {

std::optional<table> tables::get_table(std::string_view name) {
    return sync<std::optional<table>>([this, name](auto callback) { get_table_async(name, std::move(callback)); });
}

void tables::get_table_async(std::string_view name, ignite_callback<std::optional<table>> callback) {
    m_impl->get_table_async(name, std::move(callback));
}

std::optional<table> tables::get_table(const qualified_name &name) {
    return sync<std::optional<table>>([this, name](auto callback) { get_table_async(name, std::move(callback)); });
}

void tables::get_table_async(const qualified_name &name, ignite_callback<std::optional<table>> callback) {
    m_impl->get_table_async(name, std::move(callback));
}

std::vector<table> tables::get_tables() {
    return sync<std::vector<table>>([this](auto callback) { get_tables_async(std::move(callback)); });
}

void tables::get_tables_async(ignite_callback<std::vector<table>> callback) {
    m_impl->get_tables_async(std::move(callback));
}

} // namespace ignite
