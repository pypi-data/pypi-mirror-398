/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <string>

namespace ignite::network
{

/**
 * TLS/SSL configuration parameters.
 */
struct secure_configuration
{
    /** Path to file containing security certificate to use. */
    std::string cert_path;

    /** Path to file containing private key to use. */
    std::string key_path;

    /** Path to file containing Certificate authority to use. */
    std::string ca_path;
};

}


