/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <chrono>
#include <memory>
#include <string>
#include <vector>

namespace ignite {

/**
 * Represents system process launched using commandline instruction.
 */
class CmdProcess {
public:
    /**
     * Destructor.
     */
    virtual ~CmdProcess() = default;

    /**
     * Make new process instance.
     *
     * @param command Command.
     * @param args Arguments.
     * @param workDir Working directory.
     * @return CmdProcess.
     */
    static std::unique_ptr<CmdProcess> make(std::string command, std::vector<std::string> args, std::string workDir);

    /**
     * Start process.
     */
    virtual bool start() = 0;

    /**
     * Kill the process.
     */
    virtual void kill() = 0;

    /**
     * Join process.
     *
     * @param timeout Timeout.
     */
    virtual void join(std::chrono::milliseconds timeout) = 0;

protected:
    /**
     * Constructor.
     */
    CmdProcess() = default;
};

} // namespace ignite
