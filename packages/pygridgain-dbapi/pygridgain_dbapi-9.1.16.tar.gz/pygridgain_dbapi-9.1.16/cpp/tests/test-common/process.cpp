/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#ifdef _WIN32
# include "detail/win_process.h"
#else
# include "detail/unix_process.h"
#endif

#include "cmd_process.h"

#include <filesystem>
#include <utility>
#include <vector>

namespace ignite {

std::unique_ptr<CmdProcess> CmdProcess::make(std::string command, std::vector<std::string> args, std::string workDir) {
#ifdef _WIN32
    return std::make_unique<detail::WinProcess>(std::move(command), std::move(args), std::move(workDir));
#else
    return std::unique_ptr<CmdProcess>(
        new detail::UnixProcess(std::move(command), std::move(args), std::move(workDir)));
#endif
}

} // namespace ignite
