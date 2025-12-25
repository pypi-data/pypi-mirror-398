/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#pragma once

#include "ignite/client/table/table.h"
#include "ignite/client/table/qualified_name.h"

#include "ignite/common/detail/config.h"
#include "ignite/common/ignite_result.h"

#include <future>
#include <memory>
#include <optional>
#include <string_view>

namespace ignite {

namespace detail {

class tables_impl;

} // namespace detail

class ignite_client;

/**
 * @brief Ignite Table API facade.
 */
class tables {
    friend class ignite_client;

public:
    // Default
    tables() = delete;

    /**
     * Gets a table by name if it was created before.
     *
     * @param name Canonical name of the table ([schema_name].[table_name]) with SQL-parser style quotation, e.g.
     *   "public.tbl0" - the table "PUBLIC.TBL0" will be looked up,
     *   "PUBLIC.\"Tbl0\"" - "PUBLIC.Tbl0",
     *   "\"MySchema\".\"Tbl0\"" - "MySchema.Tbl0", etc.
     * @return An instance of the table with the corresponding name or @c std::nullopt if the table does not exist.
     * @throw ignite_error In case of error while trying to send a request.
     */
    IGNITE_API std::optional<table> get_table(std::string_view name);

    /**
     * Gets a table by name if it was created before asynchronously.
     *
     * @param name Canonical name of the table ([schema_name].[table_name]) with SQL-parser style quotation, e.g.
     *   "public.tbl0" - the table "PUBLIC.TBL0" will be looked up,
     *   "PUBLIC.\"Tbl0\"" - "PUBLIC.Tbl0",
     *   "\"MySchema\".\"Tbl0\"" - "MySchema.Tbl0", etc.
     * @param callback Callback to be called once the operation is complete. On success, the callback is invoked with
     *    an instance of the table with the corresponding name or @c std::nullopt if the table does not exist.
     * @throw ignite_error In case of error while trying to send a request.
     */
    IGNITE_API void get_table_async(std::string_view name, ignite_callback<std::optional<table>> callback);

    /**
     * Gets a table by name if it was created before.
     *
     * @param name Qualified name of the table.
     * @return An instance of the table with the corresponding name or @c std::nullopt if the table does not exist.
     * @throw ignite_error In case of error while trying to send a request.
     */
    IGNITE_API std::optional<table> get_table(const qualified_name &name);

    /**
     * Gets a table by name if it was created before asynchronously.
     *
     * @param name Qualified name of the table.
     * @param callback Callback to be called once the operation is complete. On success, the callback is invoked with
     *    an instance of the table with the corresponding name or @c std::nullopt if the table does not exist.
     * @throw ignite_error In case of error while trying to send a request.
     */
    IGNITE_API void get_table_async(const qualified_name &name, ignite_callback<std::optional<table>> callback);

    /**
     * Gets all tables.
     *
     * @return A vector of all tables.
     * @throw ignite_error In case of error while trying to send a request.
     */
    IGNITE_API std::vector<table> get_tables();

    /**
     * Gets all tables asynchronously.
     *
     * @param callback Callback to be called once the operation is complete. On success, the callback is invoked with
     *    a vector of all tables.
     * @throw ignite_error In case of error while trying to send a request.
     */
    IGNITE_API void get_tables_async(ignite_callback<std::vector<table>> callback);

private:
    /**
     * Constructor
     *
     * @param impl Implementation
     */
    explicit tables(std::shared_ptr<detail::tables_impl> impl)
        : m_impl(std::move(impl)) {}

    /** Implementation. */
    std::shared_ptr<detail::tables_impl> m_impl;
};

} // namespace ignite
