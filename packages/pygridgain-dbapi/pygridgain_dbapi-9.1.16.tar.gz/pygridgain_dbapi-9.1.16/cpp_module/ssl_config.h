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

/**
 * A simple SSL configuration.
 */
struct ssl_config {
    /**
     * Constructor.
     *
     * @param enabled Flag indicating whether SSL is enabled.
     * @param ssl_key SSL Keyfile.
     * @param ssl_cert SSL Certificate.
     * @param ssl_ca_cert SSL CA Certificate.
     */
    ssl_config(bool enabled, const char *ssl_key, const char *ssl_cert, const char *ssl_ca_cert)
        : m_enabled(enabled)
        , m_ssl_keyfile(ssl_key ? ssl_key : "")
        , m_ssl_certfile(ssl_cert ? ssl_cert : "")
        , m_ssl_ca_certfile(ssl_ca_cert ? ssl_ca_cert : "")
      {}

    /** Flag indicating whether SSL is enabled. */
    bool m_enabled{false};

    /** SSL Key. */
    const std::string m_ssl_keyfile;

    /** SSL Certificate. */
    const std::string m_ssl_certfile;

    /** SSL CA Certificate. */
    const std::string m_ssl_ca_certfile;
};
