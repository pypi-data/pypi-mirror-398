/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <ignite/common/detail/factory.h>
#include <ignite/common/ignite_error.h>
#include <ignite/network/data_buffer.h>

namespace ignite::network {

/**
 * Codec class.
 * Encodes and decodes data.
 */
class codec {
public:
    // Default
    virtual ~codec() = default;

    /**
     * Encode provided data.
     *
     * @param data Data to encode.
     * @return Encoded data. Returning null is ok.
     *
     * @throw ignite_error on error.
     */
    virtual data_buffer_owning encode(data_buffer_owning &data) = 0;

    /**
     * Decode provided data.
     *
     * @param data Data to decode.
     * @return Decoded data. Returning null means data is not yet ready.
     *
     * @throw ignite_error on error.
     */
    virtual data_buffer_ref decode(data_buffer_ref &data) = 0;
};

} // namespace ignite::network
