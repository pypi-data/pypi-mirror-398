/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/odbc/utility.h"
#include "ignite/protocol/reader.h"

#include <cstdint>
#include <string>
#include <utility>

namespace ignite {

/**
 * Primary key metadata.
 */
class primary_key_meta {
public:
    // Default
    primary_key_meta() = default;

    /**
     * Constructor.
     *
     * @param catalog Catalog name.
     * @param schema Schema name.
     * @param table Table name.
     * @param column Column name.
     * @param key_seq Column sequence number in key (starting with 1).
     * @param key_name Key name.
     */
    primary_key_meta(std::string catalog, std::string schema, std::string table, std::string column,
        std::int16_t key_seq, std::string key_name)
        : m_catalog(std::move(catalog))
        , m_schema(std::move(schema))
        , m_table(std::move(table))
        , m_column(std::move(column))
        , m_key_seq(key_seq)
        , m_key_name(std::move(key_name)) {}

    /**
     * Get catalog name.
     *
     * @return Catalog name.
     */
    [[nodiscard]] const std::string &get_catalog_name() const { return m_catalog; }

    /**
     * Get schema name.
     *
     * @return Schema name.
     */
    [[nodiscard]] const std::string &get_schema_name() const { return m_schema; }

    /**
     * Get table name.
     *
     * @return Table name.
     */
    [[nodiscard]] const std::string &get_table_name() const { return m_table; }

    /**
     * Get column name.
     *
     * @return Column name.
     */
    [[nodiscard]] const std::string &get_column_name() const { return m_column; }

    /**
     * Get column sequence number in key.
     *
     * @return Sequence number in key.
     */
    [[nodiscard]] std::int16_t get_key_seq() const { return m_key_seq; }

    /**
     * Get key name.
     *
     * @return Key name.
     */
    [[nodiscard]] const std::string &get_key_name() const { return m_key_name; }

private:
    /** Catalog name. */
    std::string m_catalog;

    /** Schema name. */
    std::string m_schema;

    /** Table name. */
    std::string m_table;

    /** Column name. */
    std::string m_column;

    /** Column sequence number in key. */
    std::int16_t m_key_seq{0};

    /** Key name. */
    std::string m_key_name;
};

/** Table metadata vector alias. */
typedef std::vector<primary_key_meta> primary_key_meta_vector;

} // namespace ignite
