/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include <algorithm>
#include <type_traits>

namespace ignite::detail {

template<typename D1, typename D2>
std::common_type_t<D1, D2> min(const D1& d1, const D2& d2) {
    return std::min<std::common_type_t<D1, D2>>(d1, d2);
}

template<typename D1, typename D2>
std::common_type_t<D1, D2> max(const D1& d1, const D2& d2) {
    return std::max<std::common_type_t<D1, D2>>(d1, d2);
}

} // namespace ignite::detail
