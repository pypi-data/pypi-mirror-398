/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <memory>

namespace ignite::detail {

/**
 * Factory class.
 *
 * @tparam T Instances of this type factory builds.
 */
template<typename T>
class factory {
public:
    /**
     * Destructor.
     */
    virtual ~factory() = default;

    /**
     * Build instance.
     *
     * @return New instance of type @c T.
     */
    virtual std::unique_ptr<T> build() = 0;
};

/**
 * Basic factory class.
 *
 * @tparam TB Base type.
 * @tparam TC Concrete type.
 */
template<typename TB, typename TC>
class basic_factory : public factory<TB> {
public:
    /**
     * Destructor.
     */
    virtual ~basic_factory() = default;

    /**
     * Build instance.
     *
     * @return New instance of type @c T.
     */
    [[nodiscard]] std::unique_ptr<TB> build() override { return std::make_unique<TC>(); }
};

} // namespace ignite::detail
