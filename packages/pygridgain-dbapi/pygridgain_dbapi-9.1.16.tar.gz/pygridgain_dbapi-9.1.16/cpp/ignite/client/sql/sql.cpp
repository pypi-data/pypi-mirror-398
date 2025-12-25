/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/client/sql/sql.h"
#include "ignite/client/detail/sql/sql_impl.h"

namespace ignite {

void sql::execute_async(transaction *tx, cancellation_token *token, const sql_statement &statement,
    std::vector<primitive> args, ignite_callback<result_set> callback) {
    m_impl->execute_async(tx, token, statement, std::move(args), std::move(callback));
}

void sql::execute_script_async(cancellation_token *token, const sql_statement &statement,
    std::vector<primitive> args, ignite_callback<void> callback) {
    m_impl->execute_script_async(token, statement, std::move(args), std::move(callback));
}

} // namespace ignite
