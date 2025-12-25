/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/compute/broadcast_execution.h"
#include "ignite/client/compute/broadcast_job_target.h"
#include "ignite/client/compute/job_descriptor.h"
#include "ignite/client/compute/job_execution.h"
#include "ignite/client/compute/job_target.h"
#include "ignite/common/binary_object.h"
#include "ignite/common/detail/config.h"
#include "ignite/common/ignite_result.h"

#include <memory>
#include <utility>


namespace ignite {

namespace detail {
class compute_impl;
}

/**
 * @brief Ignite Compute API facade.
 */
class compute {
    friend class ignite_client;

public:
    // Delete
    compute() = delete;

    /**
     * Submits for execution a compute job represented by the given class for an execution on the specified target.
     *
     * @param target Job target.
     * @param descriptor Descriptor.
     * @param arg Job argument.
     * @param callback A callback called on operation completion with job execution result.
     */
    IGNITE_API void submit_async(std::shared_ptr<job_target> target, std::shared_ptr<job_descriptor> descriptor,
        const binary_object &arg, ignite_callback<job_execution> callback);

    /**
     * Submits for execution a compute job represented by the given class on the specified target.
     *
     * @param target Job target.
     * @param descriptor Descriptor.
     * @param arg Job argument.
     * @return Job execution result.
     */
    IGNITE_API job_execution submit(std::shared_ptr<job_target> target, std::shared_ptr<job_descriptor> descriptor,
        const binary_object &arg) {
        return sync<job_execution>([&](auto callback) mutable {
            submit_async(std::move(target), std::move(descriptor), arg, std::move(callback));
        });
    }

    /**
     * Broadcast a compute job represented by the given class for an execution on all the specified nodes.
     *
     * @param target Job target.
     * @param descriptor Descriptor.
     * @param arg Job argument.
     * @param callback A callback called on operation completion with jobs execution result.
     */
    IGNITE_API void submit_broadcast_async(std::shared_ptr<broadcast_job_target> target,
        std::shared_ptr<job_descriptor> descriptor, const binary_object &arg,
        ignite_callback<broadcast_execution> callback);

    /**
     * Broadcast a compute job represented by the given class on all the specified nodes.
     *
     * @param target Job target.
     * @param descriptor Descriptor.
     * @param arg Job argument.
     * @return Job execution result.
     */
    IGNITE_API broadcast_execution submit_broadcast(
        std::shared_ptr<broadcast_job_target> target, std::shared_ptr<job_descriptor> descriptor,
        const binary_object &arg) {
        return sync<broadcast_execution>([&](auto callback) mutable {
            submit_broadcast_async(std::move(target), std::move(descriptor), arg, std::move(callback));
        });
    }

private:
    /**
     * Constructor.
     *
     * @param impl Implementation.
     */
    explicit compute(std::shared_ptr<detail::compute_impl> impl)
        : m_impl(std::move(impl)) {}

    /** Implementation. */
    std::shared_ptr<detail::compute_impl> m_impl;
};

} // namespace ignite
