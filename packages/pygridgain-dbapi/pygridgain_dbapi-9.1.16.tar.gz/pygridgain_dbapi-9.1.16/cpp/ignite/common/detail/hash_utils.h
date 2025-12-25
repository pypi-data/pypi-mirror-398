/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "bytes_view.h"

#include <cstdint>

namespace ignite::detail {

/**
 * Hash values
 *
 * @param data Byte sequence.
 * @return Hash for the data.
 */
std::int32_t hash32(bytes_view data) noexcept;

/**
 * Combine hashes.
 *
 * @param h1 Fist hash.
 * @param h2 Second hash.
 * @return Combined hash.
 */
std::int32_t hash_combine(std::int32_t h1, std::int32_t h2) noexcept;

} // namespace ignite::detail
