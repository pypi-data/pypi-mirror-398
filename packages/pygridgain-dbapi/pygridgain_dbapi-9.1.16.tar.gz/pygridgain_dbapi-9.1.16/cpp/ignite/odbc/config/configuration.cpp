/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/odbc/config/configuration.h"
#include "ignite/odbc/config/config_tools.h"
#include "ignite/odbc/odbc_error.h"
#include "ignite/common/detail/string_utils.h"

#include <string>

/** Configuration keys . */
namespace key {
/** Key for fetch results page size attribute. */
static inline const std::string page_size{"page_size"};

/** Key for Driver attribute. */
static inline const std::string host{"host"};

/** Key for TCP port attribute. */
static inline const std::string port{"port"};

/** Key for address attribute. */
static inline const std::string address{"address"};

/** Key for address attribute. */
static inline const std::string schema{"schema"};

/** Key for authentication identity. */
static inline const std::string identity{"identity"};

/** Key for authentication secret. */
static inline const std::string secret{"secret"};

/** Key for timezone. */
static inline const std::string timezone{"timezone"};

/** Key for SSL mode. */
static inline const std::string ssl_mode{"ssl_mode"};

/** Key for the SSL private key file path. */
static inline const std::string ssl_key_file{"ssl_key_file"};

/** Key for the SSL certificate file path. */
static inline const std::string ssl_cert_file{"ssl_cert_file"};

/** Key for the SSL certificate authority file path. */
static inline const std::string ssl_ca_file{"ssl_ca_file"};

/** Key for the heartbeat interval in ms. */
static inline const std::string heartbeat_interval{"heartbeat_interval"};

} // namespace key

namespace ignite {

void try_get_string_param(
    value_with_default<std::string> &dst, const config_map &config_params, const std::string &key) {
    auto it = config_params.find(key);
    if (it != config_params.end()) {
        dst = {it->second, true};
    }
}

template<typename T, typename V>
void try_get_int_param(
    value_with_default<V> &dst, const config_map &config_params, const std::string &key, const std::string &err_msg) {
    auto it = config_params.find(key);
    if (it != config_params.end()) {
        auto opt = detail::parse_int<T>(it->second);
        if (!opt)
            throw odbc_error(sql_state::S01S00_INVALID_CONNECTION_STRING_ATTRIBUTE,
                err_msg + it->second);

        dst = {V{*opt}, true};
    }
}

void configuration::from_config_map(const config_map &config_params) {
    *this = configuration();

    try_get_int_param<std::int32_t>(m_page_size, config_params, key::page_size, "Invalid page size value: ");

    auto address_it = config_params.find(key::address);
    if (address_it != config_params.end())
        m_end_points = {parse_address(address_it->second), true};
    else {
        end_point ep;
        auto host_it = config_params.find(key::host);
        if (host_it == config_params.end())
            throw odbc_error(
                sql_state::S01S00_INVALID_CONNECTION_STRING_ATTRIBUTE, "Connection address is not specified");

        auto host = host_it->second;
        uint16_t port = default_value::port;

        auto port_it = config_params.find(key::port);
        if (port_it != config_params.end())
            port = detail::parse_port(port_it->second);

        m_end_points = {{{host, port}}, true};
    }

    auto ssl_mode_it = config_params.find(key::ssl_mode);
    if (ssl_mode_it != config_params.end()) {
        auto ssl_mode = ssl_mode_from_string(ssl_mode_it->second);
        if (ssl_mode == ssl_mode_t::UNKNOWN) {
            throw odbc_error(sql_state::S01S00_INVALID_CONNECTION_STRING_ATTRIBUTE,
                "Unsupported SSL mode value: " + ssl_mode_it->second);
        }
        m_ssl_mode = {ssl_mode, true};
    }

    try_get_string_param(m_schema, config_params, key::schema);

    try_get_string_param(m_auth_identity, config_params, key::identity);
    try_get_string_param(m_auth_secret, config_params, key::secret);

    try_get_string_param(m_timezone, config_params, key::timezone);

    try_get_string_param(m_ssl_key_file, config_params, key::ssl_key_file);
    try_get_string_param(m_ssl_cert_file, config_params, key::ssl_cert_file);
    try_get_string_param(m_ssl_ca_file, config_params, key::ssl_ca_file);

    try_get_int_param<std::int32_t>(m_heartbeat_interval, config_params, key::heartbeat_interval,
        "Invalid heartbeat interval value: ");
    if (m_heartbeat_interval.get_value().count() < 0) {
        throw odbc_error(sql_state::S01S00_INVALID_CONNECTION_STRING_ATTRIBUTE,
            std::string("Heartbeat interval value could not be negative: ") +
            std::to_string(m_heartbeat_interval.get_value().count()));
    }
}

} // namespace ignite
