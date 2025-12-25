/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/continuous_query/continuous_query.h"
#include "ignite/client/detail/continuous_query/continuous_query_impl.h"

namespace ignite {

void continuous_query<ignite_tuple>::get_next_async(ignite_callback<table_row_event_batch<entry_type>> callback) {
    typedef detail::continuous_query_event_consumer_record<entry_type> consumer_type;
    get_next_async(std::make_shared<consumer_type>(std::move(callback)));
}

void continuous_query<ignite_tuple>::get_next_async(std::shared_ptr<detail::continuous_query_event_consumer> consumer) {
    m_impl->get_next_async(std::move(consumer));
}

bool continuous_query<ignite_tuple>::is_complete() const {
    return m_impl->is_complete();
}

void continuous_query<ignite_tuple>::cancel() {
    m_impl->cancel();
}

void continuous_query<std::pair<ignite_tuple, ignite_tuple>>::get_next_async(
    ignite_callback<table_row_event_batch<entry_type>> callback) {
    typedef detail::continuous_query_event_consumer_kv<key_type, value_type> consumer_type;
    get_next_async(std::make_shared<consumer_type>(std::move(callback)));
}

void continuous_query<std::pair<ignite_tuple, ignite_tuple>>::get_next_async(
    std::shared_ptr<detail::continuous_query_event_consumer> consumer) {
    m_impl->get_next_async(std::move(consumer));
}

bool continuous_query<std::pair<ignite_tuple, ignite_tuple>>::is_complete() const {
    return m_impl->is_complete();
}

void continuous_query<std::pair<ignite_tuple, ignite_tuple>>::cancel() {
    m_impl->cancel();
}

} // namespace ignite