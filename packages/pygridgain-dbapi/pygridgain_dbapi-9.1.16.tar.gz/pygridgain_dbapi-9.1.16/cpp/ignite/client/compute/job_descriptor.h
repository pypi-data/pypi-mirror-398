/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/compute/deployment_unit.h"
#include "ignite/client/compute/job_execution_options.h"

#include <string>
#include <utility>
#include <vector>
#include <memory>

namespace ignite {

/**
 * @brief Compute job descriptor.
 *
 * Contains necessary context to start compute job execution.
 */
class job_descriptor {
public:
    /**
     * Default constructor.
     */
    job_descriptor() = default;

    /**
     * Get job class name.
     *
     * @return Job class name.
     */
    [[nodiscard]] const std::string &get_job_class_name() const { return m_job_class_name; }

    /**
     * Get deployment units.
     *
     * @return Deployment units.
     */
    [[nodiscard]] const std::vector<deployment_unit> &get_deployment_units() const { return m_units; }

    /**
     * Get execution options.
     *
     * @return Execution options.
     */
    [[nodiscard]] const job_execution_options &get_execution_options() const { return m_options; }

    /**
     * @brief Job description builder.
     */
    class builder {
    public:
        /**
         * Constructor.
         *
         * @param job_class_name Job class name.
         */
        explicit builder(std::string job_class_name) {
            m_descriptor->m_job_class_name = std::move(job_class_name);
        }

        /**
         * Set job class name.
         *
         * @param job_class_name Job class name.
         */
        builder& job_class_name(std::string job_class_name) {
            m_descriptor->m_job_class_name = std::move(job_class_name);
            return *this;
        }

        /**
         * Set deployment units.
         *
         * @param units Deployment units to set.
         */
        builder& deployment_units(std::vector<deployment_unit> units) {
            m_descriptor->m_units = std::move(units);
            return *this;
        }

        /**
         * Set execution options.
         *
         * @param options Execution options.
         */
        builder& execution_options(job_execution_options options) {
            m_descriptor->m_options = std::move(options); // NOLINT(*-move-const-arg)
            return *this;
        }

        /**
         * Build Job Descriptor.
         *
         * @return An instance of Job Descriptor.
         */
        std::shared_ptr<job_descriptor> build() { return std::move(m_descriptor); }
    private:
        /** Descriptor. */
        std::shared_ptr<job_descriptor> m_descriptor{std::make_shared<job_descriptor>()};
    };
private:
    /** Job class name. */
    std::string m_job_class_name;

    /** Units. */
    std::vector<deployment_unit> m_units;

    /** Options. */
    job_execution_options m_options;
};

} // namespace ignite
