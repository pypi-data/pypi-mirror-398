/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "ignite_runner.h"
#include "test_utils.h"

#include <ignite/common/ignite_error.h>

#include <gtest/gtest.h>

#include <chrono>
#include <csignal>

namespace {

/** Shutdown handler that cleans up resources. */
std::function<void(int)> shutdown_handler;

/**
 * Receives OS signal and handles it.
 *
 * @param signum Signal value.
 */
void signal_handler(int signum) {
    shutdown_handler(signum);
    signal(signum, SIG_DFL);
    raise(signum);
}

} // namespace

/**
 * Sets process abortion (SIGABRT, SIGINT, SIGSEGV signals) handler.
 *
 * @param handler Abortion handler.
 */
void set_process_abort_handler(std::function<void(int)> handler) {
    shutdown_handler = std::move(handler);

    // Install signal handlers to clean up resources on early exit.
    signal(SIGABRT, signal_handler);
    signal(SIGINT, signal_handler);
    signal(SIGSEGV, signal_handler);
}

int main(int argc, char **argv) {
    using namespace ignite;

    if (ignite_runner::single_node_mode())
        std::cout << "Tests run in a single-node mode." << std::endl;
    else
        std::cout << "Tests run in a multi-node mode." << std::endl;

    ignite_runner runner;
    set_process_abort_handler([&](int signal) {
        std::cout << "Caught signal " << signal << " during tests" << std::endl;

        runner.stop();
    });

    if (!check_test_node_connectable(std::chrono::seconds(5))) {
        runner.start();
        ensure_node_connectable(std::chrono::seconds(60));
    }

    try {
        ::testing::InitGoogleTest(&argc, argv);
        [[maybe_unused]] int run_res = RUN_ALL_TESTS();
    } catch (const std::exception &err) {
        std::cout << "Uncaught error: " << err.what() << std::endl;
        return 1;
    } catch (...) {
        std::cout << "Unknown uncaught error" << std::endl;
        return 2;
    }

    return 0;
}
