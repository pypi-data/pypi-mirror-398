/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/sql/result_set.h"
#include "ignite/client/detail/sql/result_set_impl.h"

namespace ignite {

const result_set_metadata &result_set::metadata() const {
    return m_impl->metadata();
}

bool result_set::has_rowset() const {
    return m_impl->has_rowset();
}

std::int64_t result_set::affected_rows() const {
    return m_impl->affected_rows();
}

bool result_set::was_applied() const {
    return m_impl->was_applied();
}

bool result_set::close_async(std::function<void(ignite_result<void>)> callback) {
    return m_impl->close_async(std::move(callback));
}

bool result_set::close() {
    return m_impl->close();
}

std::vector<ignite_tuple> result_set::current_page() && {
    return std::move(*m_impl).current_page();
}

const std::vector<ignite_tuple> &result_set::current_page() const & {
    return m_impl->current_page();
}

bool result_set::has_more_pages() {
    return m_impl->has_more_pages();
}

void result_set::fetch_next_page_async(std::function<void(ignite_result<void>)> callback) {
    m_impl->fetch_next_page_async(std::move(callback));
}

} // namespace ignite
