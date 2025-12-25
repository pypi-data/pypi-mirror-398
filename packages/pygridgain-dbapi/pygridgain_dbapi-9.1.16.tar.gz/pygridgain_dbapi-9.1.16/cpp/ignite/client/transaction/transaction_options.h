/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

namespace ignite {
/**
 * @brief Transaction options.
 */
class transaction_options {
public:
    /**
     * Transaction timeout.
     *
     * @return Transaction timeout in milliseconds.
     */
    [[nodiscard]] std::int64_t get_timeout_millis() const { return m_timeout_millis; }

    /**
     * Sets new value for transaction timeout.
     *
     * @param timeout_millis Transaction timeout in milliseconds.
     * @return Reference to this for chaining.
     */
    transaction_options &set_timeout_millis(std::int64_t timeout_millis) {
        m_timeout_millis = timeout_millis;
        return *this;
    }

    /**
     * Transaction allow only read operations.
     *
     * @return True if only read operation are allowed false otherwise.
     */
    [[nodiscard]] bool is_read_only() const { return m_read_only; }

    /**
     * Change transaction to be read-only or read-write.
     *
     * @param read_only True if transaction should read-only, false if read-write.
     * @return Reference to this for chaining.
     */
    transaction_options &set_read_only(bool read_only) {
        m_read_only = read_only;
        return *this;
    }

private:
    std::int64_t m_timeout_millis = 0;
    bool m_read_only = false;
};
} // namespace ignite
