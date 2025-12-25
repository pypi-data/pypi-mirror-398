/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/ignite_client_authenticator.h"

#include <string>

namespace ignite {

/**
 * @brief Basic authenticator with username and password.
 *
 * Credentials are sent to the server in plain text, unless SSL/TLS is enabled.
 */
class basic_authenticator : public ignite_client_authenticator {
public:
    /** Type constant. */
    inline static const std::string TYPE{"basic"};

    // Default
    basic_authenticator() = default;

    /**
     * Constructor.
     *
     * @param username Username.
     * @param password Password.
     */
    basic_authenticator(std::string username, std::string password)
        : m_username(std::move(username))
        , m_password(std::move(password)) {}

    /**
     * Get authenticator type.
     *
     * @return Authenticator type.
     */
    [[nodiscard]] const std::string &get_type() const override { return TYPE; }

    /**
     * Get identity.
     *
     * @return Username.
     */
    [[nodiscard]] const std::string &get_identity() const override { return m_username; }

    /**
     * Set username.
     *
     * @param username Username.
     */
    void set_username(std::string username) { m_username = std::move(username); };

    /**
     * Get secret.
     *
     * @return Password.
     */
    [[nodiscard]] const std::string &get_secret() const override { return m_password; }

    /**
     * Set password.
     *
     * @param password Password.
     */
    void set_password(std::string password) { m_password = std::move(password); };

private:
    /** Username. */
    std::string m_username;

    /** Password. */
    std::string m_password;
};

} // namespace ignite
