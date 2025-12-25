/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/transaction/transactions.h"
#include "ignite/client/detail/transaction/transactions_impl.h"

namespace ignite {

void transactions::begin_async(transaction_options tx_opts, ignite_callback<transaction> callback) {
    m_impl->begin_async(tx_opts, std::move(callback));
}

void transactions::begin_async(ignite_callback<transaction> callback) {
    m_impl->begin_async({}, std::move(callback));
}

} // namespace ignite
