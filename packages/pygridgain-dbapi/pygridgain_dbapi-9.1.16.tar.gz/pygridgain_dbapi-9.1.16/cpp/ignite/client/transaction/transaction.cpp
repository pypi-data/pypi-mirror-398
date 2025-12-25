/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/transaction/transaction.h"
#include "ignite/client/detail/transaction/transaction_impl.h"

namespace ignite {

void transaction::commit_async(const ignite_callback<void> &callback) {
    m_impl->commit_async(callback);
}

void transaction::rollback_async(const ignite_callback<void> &callback) {
    m_impl->rollback_async(callback);
}

} // namespace ignite
