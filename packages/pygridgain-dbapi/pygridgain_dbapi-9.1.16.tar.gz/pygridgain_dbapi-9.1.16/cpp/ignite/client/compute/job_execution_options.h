/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <cstdint>

namespace ignite {

/**
 * @brief Job execution options.
 */
class job_execution_options {
public:
    /**
     * Default constructor.
     *
     * Default options:
     * priority = 0;
     * max_retries = 0;
     */
    job_execution_options() = default;

    /**
     * Constructor.
     *
     * @param priority Job execution priority.
     * @param max_retries Max number of times to retry job execution in case of failure, 0 to not retry.
     */
    explicit job_execution_options(std::int32_t priority, std::int32_t max_retries)
        : m_priority(priority)
        , m_max_retries(max_retries) {}

    /**
     * Gets the job execution priority.
     *
     * @return Job execution priority.
     */
    [[nodiscard]] std::int32_t get_priority() const { return m_priority; }

    /**
     * Gets the max number of times to retry job execution in case of failure, 0 to not retry.
     *
     * @return Max number of times to retry job execution in case of failure, 0 to not retry.
     */
    [[nodiscard]] std::int32_t get_max_retries() const { return m_max_retries; }

private:
    /** Job execution priority. */
    std::int32_t m_priority{0};

    /** Max re-tries. */
    std::int32_t m_max_retries{0};
};

} // namespace ignite
