/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/sql/column_metadata.h"

#include <string>
#include <unordered_map>
#include <vector>

namespace ignite {

/**
 * @brief SQL result set metadata.
 */
class result_set_metadata {
public:
    // Default
    result_set_metadata() = default;

    /**
     * Constructor.
     *
     * @param columns Columns.
     */
    result_set_metadata(std::vector<column_metadata> columns)
        : m_columns(std::move(columns)) {}

    /**
     * Gets the columns in the same order as they appear in the result set data.
     *
     * @return The columns metadata.
     */
    [[nodiscard]] const std::vector<column_metadata> &columns() const { return m_columns; }

    /**
     * Gets the index of the specified column, or -1 when there is no column
     * with the specified name.
     *
     * @param name The column name.
     * @return Column index.
     */
    [[nodiscard]] std::int32_t index_of(const std::string &name) const {
        if (m_indices.empty()) {
            for (size_t i = 0; i < m_columns.size(); ++i) {
                m_indices[m_columns[i].name()] = i;
            }
        }

        auto it = m_indices.find(name);
        if (it == m_indices.end())
            return -1;
        return std::int32_t(it->second);
    }

private:
    /** Columns metadata. */
    std::vector<column_metadata> m_columns;

    /** Indices of the columns corresponding to their names. */
    mutable std::unordered_map<std::string, size_t> m_indices;
};

} // namespace ignite
