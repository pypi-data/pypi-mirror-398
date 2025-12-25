/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include <ignite/client/ignite_client_configuration.h>
#include <ignite/client/detail/argument_check_utils.h>


namespace ignite {

void ignite_client_configuration::check_endpoints_non_empty(const std::vector<std::string>& endpoints) {
    detail::arg_check::container_non_empty(endpoints, "Connection endpoint list");
}

} // namespace ignite
