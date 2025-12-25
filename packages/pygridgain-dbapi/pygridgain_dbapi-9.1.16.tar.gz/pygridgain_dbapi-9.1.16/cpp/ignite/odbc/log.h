/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <fstream>
#include <mutex>
#include <sstream>
#include <string>

#define LOG_MSG(param)                                                                                                 \
 do {                                                                                                                  \
  if (ignite::odbc_logger *p = ignite::odbc_logger::get()) {                                                           \
   ignite::log_stream lstream(p);                                                                                      \
   lstream << __FUNCTION__ << ": " << param;                                                                           \
  }                                                                                                                    \
 } while (false)

#define TRACE_MSG(param)                                                                                               \
 do {                                                                                                                  \
  ignite::odbc_logger *p = ignite::odbc_logger::get();                                                                 \
  if (p && p->is_trace_enabled()) {                                                                                    \
   ignite::log_stream lstream(p);                                                                                      \
   lstream << __FUNCTION__ << ": " << param;                                                                           \
  }                                                                                                                    \
 } while (false)

namespace ignite {

/* Forward declaration */
class odbc_logger;

/**
 * Helper object providing stream operations for single log line.
 * Writes resulting string to odbc_logger object upon destruction.
 */
class log_stream : public std::basic_ostream<char> {
public:
    // Delete
    log_stream(log_stream &&) = delete;
    log_stream(const log_stream &) = delete;
    log_stream &operator=(log_stream &&) = delete;
    log_stream &operator=(const log_stream &) = delete;

    /**
     * Constructor.
     * @param parent pointer to odbc_logger.
     */
    explicit log_stream(odbc_logger *parent)
        : std::basic_ostream<char>(nullptr)
        , m_string_buf()
        , m_logger(parent) {
        init(&m_string_buf);
    }

    /**
     * Conversion operator helpful to determine if log is enabled
     * @return True if logger is enabled
     */
    bool operator()() { return m_logger != nullptr; }

    /**
     * Destructor.
     */
    ~log_stream() override;

private:
    /** String buffer. */
    std::basic_stringbuf<char> m_string_buf{};

    /** Parent logger object */
    odbc_logger *m_logger{nullptr};
};

/**
 * Logging facility.
 */
class odbc_logger {
public:
    // Delete
    odbc_logger(odbc_logger &&) = delete;
    odbc_logger(const odbc_logger &) = delete;
    odbc_logger &operator=(odbc_logger &&) = delete;
    odbc_logger &operator=(const odbc_logger &) = delete;

    /**
     * Get instance of odbc_logger, if enabled.
     *
     * @return odbc_logger instance if logging is enabled. Null otherwise.
     */
    static odbc_logger *get();

    /**
     * Checks if logging is enabled.
     *
     * @return True, if logging is enabled.
     */
    [[nodiscard]] bool is_enabled() const;

    /**
     * Checks if tracing is enabled.
     *
     * @return True, if tracing is enabled.
     */
    [[nodiscard]] bool is_trace_enabled() const { return m_trace_enabled; }

    /**
     * Outputs the message to log file
     * @param message The message to write
     */
    void write_message(std::string const &message);

private:
    /**
     * Constructor.
     *
     * @param path to log file.
     * @param trace_enabled Tracing enabled.
     */
    odbc_logger(const char *path, bool trace_enabled);

    /**
     * Destructor.
     */
    ~odbc_logger() = default;

    /** Mutex for writes synchronization. */
    std::mutex m_mutex{};

    /** File stream. */
    std::ofstream m_stream{};

    /** Trace enabled. */
    bool m_trace_enabled{false};
};

} // namespace ignite
