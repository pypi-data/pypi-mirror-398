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

namespace ignite {

/**
 * @brief Ignite client authenticator.
 *
 * Provides authentication information during handshake.
 */
class ignite_client_authenticator {
public:
    /**
     * Get authenticator type.
     *
     * @return Authenticator type.
     */
    [[nodiscard]] virtual const std::string &get_type() const = 0;

    /**
     * Get identity.
     *
     * @return Identity.
     */
    [[nodiscard]] virtual const std::string &get_identity() const = 0;

    /**
     * Get secret.
     *
     * @return Secret.
     */
    [[nodiscard]] virtual const std::string &get_secret() const = 0;

protected:
    // Default
    ignite_client_authenticator() = default;
    virtual ~ignite_client_authenticator() = default;
};

} // namespace ignite
