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
 * Table metadata.
 */
class table_meta {
public:
    // Default.
    table_meta() = default;

    /**
     * Constructor.
     *
     * @param catalog_name Catalog name.
     * @param schema_name Schema name.
     * @param table_name Table name.
     * @param table_type Table type.
     */
    table_meta(std::string catalog_name, std::string schema_name, std::string table_name, std::string table_type)
        : catalog_name(std::move(catalog_name))
        , schema_name(std::move(schema_name))
        , table_name(std::move(table_name))
        , table_type(std::move(table_type)) {}

    /**
     * Read using reader.
     *
     * @param reader Reader.
     */
    void read(protocol::reader &reader);

    /**
     * Get catalog name.
     *
     * @return Catalog name.
     */
    [[nodiscard]] const std::string &get_catalog_name() const { return catalog_name; }

    /**
     * Get schema name.
     *
     * @return Schema name.
     */
    [[nodiscard]] const std::string &get_schema_name() const { return schema_name; }

    /**
     * Get table name.
     *
     * @return Table name.
     */
    [[nodiscard]] const std::string &get_table_name() const { return table_name; }

    /**
     * Get table type.
     *
     * @return Table type.
     */
    [[nodiscard]] const std::string &get_table_type() const { return table_type; }

private:
    /** Catalog name. */
    std::string catalog_name;

    /** Schema name. */
    std::string schema_name;

    /** Table name. */
    std::string table_name;

    /** Table type. */
    std::string table_type;
};

/** Table metadata vector alias. */
typedef std::vector<table_meta> table_meta_vector;

/**
 * Read tables metadata collection.
 *
 * @param reader Reader.
 * @return Meta vector.
 */
table_meta_vector read_table_meta_vector(protocol::reader &reader);

} // namespace ignite
