/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite/odbc/log.h"

#include <cstdlib>

namespace ignite {

log_stream::~log_stream() {
    if (m_logger)
        m_logger->write_message(m_string_buf.str());
}

odbc_logger::odbc_logger(const char *path, bool trace_enabled)
    : m_trace_enabled(trace_enabled) {
    if (path)
        m_stream.open(path);
}

bool odbc_logger::is_enabled() const {
    return m_stream.is_open();
}

void odbc_logger::write_message(std::string const &message) {
    if (is_enabled()) {
        std::lock_guard<std::mutex> guard(m_mutex);
        m_stream << message << std::endl;
    }
}

odbc_logger *odbc_logger::get() {
    const char *env_var_path = "IGNITE3_ODBC_LOG_PATH";
    const char *env_var_trace = "IGNITE3_ODBC_LOG_TRACE_ENABLED";
    static odbc_logger logger(getenv(env_var_path), getenv(env_var_trace) != nullptr);
    return logger.is_enabled() ? &logger : nullptr;
}

} // namespace ignite
