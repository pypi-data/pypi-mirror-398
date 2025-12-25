/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "network.h"

#include "async_client_pool_adapter.h"
#include "ssl/secure_socket_client.h"

#include "ignite/common/detail/config.h"

#ifdef _WIN32
# include "detail/win/tcp_socket_client.h"
# include "detail/win/win_async_client_pool.h"
#else
# include "detail/linux/linux_async_client_pool.h"
# include "detail/linux/tcp_socket_client.h"
#endif

# include "ignite/network/ssl/ssl_gateway.h"

namespace ignite::network {

std::unique_ptr<socket_client> make_tcp_socket_client() {
    return std::make_unique<tcp_socket_client>();
}

std::shared_ptr<async_client_pool> make_async_client_pool(data_filters filters) {
    auto pool =
        std::make_shared<IGNITE_SWITCH_WIN_OTHER(detail::win_async_client_pool, detail::linux_async_client_pool)>();

    return std::make_shared<async_client_pool_adapter>(std::move(filters), std::move(pool));
}

void ensure_ssl_loaded()
{
    ssl_gateway::get_instance().load_all();
}

std::unique_ptr<socket_client> make_secure_socket_client(secure_configuration cfg)
{
    ensure_ssl_loaded();

    return std::make_unique<secure_socket_client>(std::move(cfg));
}

} // namespace ignite::network
