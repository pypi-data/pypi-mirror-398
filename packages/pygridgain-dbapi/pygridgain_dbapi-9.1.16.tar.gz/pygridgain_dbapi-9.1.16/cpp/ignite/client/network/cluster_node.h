/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/common/end_point.h"
#include "ignite/common/uuid.h"

#include <type_traits>

namespace ignite {

/**
 * @brief Abstraction for Ignite cluster node.
 */
class cluster_node {
public:
    // Default
    cluster_node() = default;

    /**
     * Constructor.
     *
     * @param id Local ID.
     * @param name Name.
     * @param address Address.
     */
    cluster_node(uuid id, std::string name, end_point address)
        : m_id(id)
        , m_name(std::move(name))
        , m_address(std::move(address)) {}

    /**
     * Gets the local node id. Changes after node restart.
     *
     * @return Local node id.
     */
    [[nodiscard]] const uuid &get_id() const { return m_id; }

    /**
     * Gets the unique name of the cluster member. Does not change after node restart.
     *
     * @return Unique name of the cluster member.
     */
    [[nodiscard]] const std::string &get_name() const { return m_name; }

    /**
     * Gets the node address.
     *
     * @return Node address.
     */
    [[nodiscard]] const end_point &get_address() const { return m_address; }

    /**
     * compare to another instance.
     *
     * @param other Another instance.
     * @return Negative value if less, positive if larger and zero, if equals
     *   another instance.
     */
    [[nodiscard]] int compare(const cluster_node &other) const {
        auto name_comp = m_name.compare(other.m_name);
        if (name_comp)
            return name_comp;

        auto id_comp = m_id.compare(other.m_id);
        if (id_comp)
            return id_comp;

        return m_address.compare(other.m_address);
    }

private:
    /** Local ID. */
    uuid m_id{};

    /** Name. */
    std::string m_name{};

    /** Address. */
    end_point m_address{};
};

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if equal.
 */
inline bool operator==(const cluster_node &val1, const cluster_node &val2) {
    return val1.compare(val2) == 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if not equal.
 */
inline bool operator!=(const cluster_node &val1, const cluster_node &val2) {
    return !(val1 == val2);
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if less.
 */
inline bool operator<(const cluster_node &val1, const cluster_node &val2) {
    return val1.compare(val2) < 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if less or equal.
 */
inline bool operator<=(const cluster_node &val1, const cluster_node &val2) {
    return val1.compare(val2) <= 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if greater.
 */
inline bool operator>(const cluster_node &val1, const cluster_node &val2) {
    return val1.compare(val2) > 0;
}

/**
 * Comparison operator.
 *
 * @param val1 First value.
 * @param val2 Second value.
 * @return True if greater or equal.
 */
inline bool operator>=(const cluster_node &val1, const cluster_node &val2) {
    return val1.compare(val2) >= 0;
}

} // namespace ignite
