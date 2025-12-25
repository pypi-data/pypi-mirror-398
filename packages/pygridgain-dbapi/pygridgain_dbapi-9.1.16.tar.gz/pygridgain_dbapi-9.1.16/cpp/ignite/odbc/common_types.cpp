/*
 *  Copyright (C) GridGain Systems. All Rights Reserved.
 *  _________        _____ __________________        _____
 *  __  ____/___________(_)______  /__  ____/______ ____(_)_______
 *  _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
 *  / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
 *  \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
 */

#include "common_types.h"
#include "ignite/odbc/system/odbc_constants.h"

namespace ignite {

SQLRETURN sql_result_to_return_code(sql_result result) {
    switch (result) {
        case sql_result::AI_SUCCESS:
            return SQL_SUCCESS;

        case sql_result::AI_SUCCESS_WITH_INFO:
            return SQL_SUCCESS_WITH_INFO;

        case sql_result::AI_NO_DATA:
            return SQL_NO_DATA;

        case sql_result::AI_NEED_DATA:
            return SQL_NEED_DATA;

        case sql_result::AI_ERROR:
        default:
            return SQL_ERROR;
    }
}

diagnostic_field diagnostic_field_to_internal(int16_t field) {
    switch (field) {
        case SQL_DIAG_CURSOR_ROW_COUNT:
            return diagnostic_field::HEADER_CURSOR_ROW_COUNT;

        case SQL_DIAG_DYNAMIC_FUNCTION:
            return diagnostic_field::HEADER_DYNAMIC_FUNCTION;

        case SQL_DIAG_DYNAMIC_FUNCTION_CODE:
            return diagnostic_field::HEADER_DYNAMIC_FUNCTION_CODE;

        case SQL_DIAG_NUMBER:
            return diagnostic_field::HEADER_NUMBER;

        case SQL_DIAG_RETURNCODE:
            return diagnostic_field::HEADER_RETURN_CODE;

        case SQL_DIAG_ROW_COUNT:
            return diagnostic_field::HEADER_ROW_COUNT;

        case SQL_DIAG_CLASS_ORIGIN:
            return diagnostic_field::STATUS_CLASS_ORIGIN;

        case SQL_DIAG_COLUMN_NUMBER:
            return diagnostic_field::STATUS_COLUMN_NUMBER;

        case SQL_DIAG_CONNECTION_NAME:
            return diagnostic_field::STATUS_CONNECTION_NAME;

        case SQL_DIAG_MESSAGE_TEXT:
            return diagnostic_field::STATUS_MESSAGE_TEXT;

        case SQL_DIAG_NATIVE:
            return diagnostic_field::STATUS_NATIVE;

        case SQL_DIAG_ROW_NUMBER:
            return diagnostic_field::STATUS_ROW_NUMBER;

        case SQL_DIAG_SERVER_NAME:
            return diagnostic_field::STATUS_SERVER_NAME;

        case SQL_DIAG_SQLSTATE:
            return diagnostic_field::STATUS_SQLSTATE;

        case SQL_DIAG_SUBCLASS_ORIGIN:
            return diagnostic_field::STATUS_SUBCLASS_ORIGIN;

        default:
            break;
    }

    return diagnostic_field::UNKNOWN;
}

environment_attribute environment_attribute_to_internal(int32_t attr) {
    switch (attr) {
        case SQL_ATTR_ODBC_VERSION:
            return environment_attribute::ODBC_VERSION;

        case SQL_ATTR_OUTPUT_NTS:
            return environment_attribute::OUTPUT_NTS;

        default:
            break;
    }

    return environment_attribute::UNKNOWN;
}

sql_state error_code_to_sql_state(error::code code) {
    switch (code) {
        // Common group. Group code: 1
        case error::code::CURSOR_ALREADY_CLOSED:
        case error::code::RESOURCE_CLOSING:
            return sql_state::S24000_INVALID_CURSOR_STATE;
        case error::code::NODE_STOPPING:
        case error::code::COMPONENT_NOT_STARTED:
        case error::code::ILLEGAL_ARGUMENT:
        case error::code::USER_OBJECT_SERIALIZATION:
        case error::code::SSL_CONFIGURATION:
        case error::code::NODE_LEFT:
        case error::code::INTERNAL:
        case error::code::NULLABLE_VALUE:
        case error::code::UNSUPPORTED_TABLE_BASED_REPLICATION:
            return sql_state::SHY000_GENERAL_ERROR;

        // Table group. Group code: 2
        case error::code::TABLE_ALREADY_EXISTS:
            return sql_state::S42S01_TABLE_OR_VIEW_ALREADY_EXISTS;
        case error::code::TABLE_NOT_FOUND:
            return sql_state::S42S02_TABLE_OR_VIEW_NOT_FOUND;
        case error::code::COLUMN_ALREADY_EXISTS:
            return sql_state::S42S21_COLUMN_ALREADY_EXISTS;
        case error::code::COLUMN_NOT_FOUND:
            return sql_state::S42S22_COLUMN_NOT_FOUND;
        case error::code::SCHEMA_VERSION_MISMATCH:
        case error::code::UNSUPPORTED_PARTITION_TYPE:
            return sql_state::SHY000_GENERAL_ERROR;

        // Client group. Group code: 3
        case error::code::CONNECTION:
        case error::code::PROTOCOL:
        case error::code::PROTOCOL_COMPATIBILITY:
        case error::code::SERVER_TO_CLIENT_REQUEST:
            return sql_state::S08001_CANNOT_CONNECT;
        case error::code::TABLE_ID_NOT_FOUND:
            return sql_state::S42S02_TABLE_OR_VIEW_NOT_FOUND;
        case error::code::CONFIGURATION:
        case error::code::CLUSTER_ID_MISMATCH:
        case error::code::CLIENT_SSL_CONFIGURATION:
        case error::code::HANDSHAKE_HEADER:
            return sql_state::S08004_CONNECTION_REJECTED;
        case error::code::RESOURCE_NOT_FOUND:
        case error::code::OPERATION_TIMEOUT:
            return sql_state::SHY000_GENERAL_ERROR;

        // Sql group. Group code: 4
        case error::code::SCHEMA_NOT_FOUND:
            return sql_state::S3F000_INVALID_SCHEMA_NAME;
        case error::code::EXECUTION_CANCELLED:
            return sql_state::SHY008_OPERATION_CANCELED;
        case error::code::TX_CONTROL_INSIDE_EXTERNAL_TX:
            return sql_state::S25000_INVALID_TRANSACTION_STATE;
        case error::code::CONSTRAINT_VIOLATION:
            return sql_state::S23000_INTEGRITY_CONSTRAINT_VIOLATION;
        case error::code::STMT_PARSE:
            return sql_state::S42000_SYNTAX_ERROR_OR_ACCESS_VIOLATION;
        case error::code::STMT_VALIDATION:
            return sql_state::S42000_SYNTAX_ERROR_OR_ACCESS_VIOLATION;
        case error::code::QUERY_NO_RESULT_SET:
        case error::code::RUNTIME:
        case error::code::MAPPING:
            return sql_state::SHY000_GENERAL_ERROR;

        // MetaStorage group. Group code: 5
        case error::code::OP_EXECUTION:
        case error::code::OP_EXECUTION_TIMEOUT:
            return sql_state::SHYT00_TIMEOUT_EXPIRED;
        case error::code::STARTING_STORAGE:
        case error::code::RESTORING_STORAGE:
        case error::code::COMPACTION:
            return sql_state::SHY000_GENERAL_ERROR;
        case error::code::COMPACTED:
        case error::code::DIVERGED:
            return sql_state::SHY000_GENERAL_ERROR;

        // Index group. Group code: 6
        case error::code::INDEX_NOT_FOUND:
            return sql_state::S42S12_INDEX_NOT_FOUND;
        case error::code::INDEX_ALREADY_EXISTS:
            return sql_state::S42S11_INDEX_ALREADY_EXISTS;

        // Transactions group. Group code: 7
        case error::code::TX_STATE_STORAGE:
        case error::code::TX_STATE_STORAGE_STOPPED:
        case error::code::TX_UNEXPECTED_STATE:
        case error::code::ACQUIRE_LOCK:
        case error::code::ACQUIRE_LOCK_TIMEOUT:
        case error::code::TX_COMMIT:
        case error::code::TX_ROLLBACK:
        case error::code::TX_FAILED_READ_WRITE_OPERATION:
        case error::code::TX_STATE_STORAGE_REBALANCE:
        case error::code::TX_READ_ONLY_TOO_OLD:
        case error::code::TX_INCOMPATIBLE_SCHEMA:
        case error::code::TX_PRIMARY_REPLICA_EXPIRED:
        case error::code::TX_ALREADY_FINISHED:
        case error::code::TX_STALE_OPERATION:
        case error::code::TX_STALE_READ_ONLY_OPERATION:
        case error::code::TX_ALREADY_FINISHED_WITH_TIMEOUT:
        case error::code::TX_DELAYED_ACK:
            return sql_state::S25000_INVALID_TRANSACTION_STATE;

        // Replicator group. Group code: 8
        case error::code::CURSOR_CLOSE:
            return sql_state::S24000_INVALID_CURSOR_STATE;
        case error::code::REPLICA_TIMEOUT:
            return sql_state::SHYT00_TIMEOUT_EXPIRED;
        case error::code::REPLICA_COMMON:
        case error::code::REPLICA_IS_ALREADY_STARTED:
        case error::code::REPLICA_UNSUPPORTED_REQUEST:
        case error::code::REPLICA_UNAVAILABLE:
        case error::code::REPLICA_MISS:
        case error::code::REPLICA_STOPPING:
        case error::code::GROUP_OVERLOADED:
            return sql_state::SHY000_GENERAL_ERROR;

        // Storage group. Group code: 9
        case error::code::INDEX_NOT_BUILT:
        case error::code::STORAGE_CORRUPTED:
            return sql_state::SHY000_GENERAL_ERROR;

        // DistributionZones group. Group code: 10
        case error::code::ZONE_NOT_FOUND:
        case error::code::EMPTY_DATA_NODES:
            return sql_state::SHY000_GENERAL_ERROR;

        // Network group. Group code: 11
        case error::code::UNRESOLVABLE_CONSISTENT_ID:
        case error::code::BIND:
        case error::code::FILE_TRANSFER:
        case error::code::FILE_VALIDATION:
        case error::code::RECIPIENT_LEFT:
        case error::code::ADDRESS_UNRESOLVED:
            return sql_state::S08001_CANNOT_CONNECT;

        // NodeConfiguration group. Group code: 12
        case error::code::CONFIG_READ:
        case error::code::CONFIG_FILE_CREATE:
        case error::code::CONFIG_WRITE:
        case error::code::CONFIG_PARSE:
        case error::code::JOIN_DENIED:
            return sql_state::SHY000_GENERAL_ERROR;

        // CodeDeployment group. Group code: 13
        case error::code::UNIT_NOT_FOUND:
        case error::code::UNIT_ALREADY_EXISTS:
        case error::code::UNIT_CONTENT_READ:
        case error::code::UNIT_UNAVAILABLE:
        case error::code::UNIT_ZIP:
        case error::code::UNIT_WRITE:
            return sql_state::SHY000_GENERAL_ERROR;

        // GarbageCollector group. Group code: 14
        case error::code::CLOSED:
            return sql_state::SHY000_GENERAL_ERROR;

        // Authentication group. Group code: 15
        case error::code::UNSUPPORTED_AUTHENTICATION_TYPE:
        case error::code::INVALID_CREDENTIALS:
        case error::code::BASIC_PROVIDER:
            return sql_state::S08004_CONNECTION_REJECTED;

        // Compute group. Group code: 16
        case error::code::CLASS_PATH:
        case error::code::CLASS_LOADER:
        case error::code::CLASS_INITIALIZATION:
        case error::code::QUEUE_OVERFLOW:
        case error::code::COMPUTE_JOB_STATUS_TRANSITION:
        case error::code::CANCELLING:
        case error::code::RESULT_NOT_FOUND:
        case error::code::FAIL_TO_GET_JOB_STATE:
        case error::code::COMPUTE_JOB_FAILED:
        case error::code::PRIMARY_REPLICA_RESOLVE:
        case error::code::CHANGE_JOB_PRIORITY:
        case error::code::NODE_NOT_FOUND:
        case error::code::MARSHALLING_TYPE_MISMATCH:
        case error::code::COMPUTE_JOB_CANCELLED:
        case error::code::COMPUTE_PLATFORM_EXECUTOR:
        case error::code::FAIL_TO_GET_JOB_OWNER:
            return sql_state::SHY000_GENERAL_ERROR;

        // Catalog group. Group code: 17
        case error::code::VALIDATION:
            return sql_state::SHY000_GENERAL_ERROR;

        // PlacementDriver group. Group code: 18
        case error::code::PRIMARY_REPLICA_AWAIT_TIMEOUT:
            return sql_state::SHYT00_TIMEOUT_EXPIRED;
        case error::code::PRIMARY_REPLICA_AWAIT:
        case error::code::EMPTY_ASSIGNMENTS:
            return sql_state::SHY000_GENERAL_ERROR;

        // CriticalWorkers group. Group code: 19
        case error::code::SYSTEM_WORKER_BLOCKED:
        case error::code::SYSTEM_CRITICAL_OPERATION_TIMEOUT:
            return sql_state::SHY000_GENERAL_ERROR;

        // DisasterRecovery group. Group code: 20
        case error::code::NODES_NOT_FOUND:
        case error::code::ILLEGAL_PARTITION_ID:
        case error::code::PARTITION_STATE:
        case error::code::CLUSTER_NOT_IDLE:
        case error::code::NOT_ENOUGH_ALIVE_NODES:
        case error::code::ILLEGAL_NODES_SET:
        case error::code::REQUEST_FORWARD:
            return sql_state::SHY000_GENERAL_ERROR;

        // Embedded group. Group code: 21
        case error::code::CLUSTER_NOT_INITIALIZED:
        case error::code::CLUSTER_INIT_FAILED:
        case error::code::NODE_NOT_STARTED:
        case error::code::NODE_START:
            return sql_state::SHY000_GENERAL_ERROR;

        // Marshalling group. Group code: 22
        case error::code::COMMON:
        case error::code::UNSUPPORTED_OBJECT_TYPE:
        case error::code::UNMARSHALLING:
            return sql_state::SHY000_GENERAL_ERROR;

        // REST service group. Group code: 23
        case error::code::CLUSTER_NOT_INIT:
            return sql_state::SHY000_GENERAL_ERROR;

        // Configuration group. Group code: 24
        case error::code::CONFIGURATION_APPLY:
        case error::code::CONFIGURATION_PARSE:
        case error::code::CONFIGURATION_VALIDATION:
            return sql_state::SHY000_GENERAL_ERROR;

        // Rbac group. Group code: 1001
        case error::code::AUTHORIZATION_FAILED:
            return sql_state::S28000_INVALID_AUTHORIZATION_SPECIFICATION;
        case error::code::COMMON_RBAC:
        case error::code::USER_NOT_FOUND:
        case error::code::USER_VALIDATION:
        case error::code::USER_ALREADY_EXISTS:
        case error::code::USER_UPDATE:
        case error::code::USER_ASSIGNMENT_EXISTS:
        case error::code::ROLE_NOT_FOUND:
        case error::code::ROLE_ALREADY_EXISTS:
        case error::code::ROLE_VALIDATION:
        case error::code::ROLE_ASSIGNMENT_NOT_FOUND:
        case error::code::ROLE_ASSIGNMENT_EXISTS:
        case error::code::ROLE_GRANTED:
        case error::code::ILLEGAL_PRIVILEGE:
        case error::code::ILLEGAL_PRIVILEGE_SELECTOR:
        case error::code::SYSTEM_USER_MODIFICATION:
            return sql_state::SHY000_GENERAL_ERROR;

        // Security group. Group code: 1002
        case error::code::COMMON_SECURITY:
        case error::code::SECURITY_CONTEXT_NOT_SET:
            return sql_state::SHY000_GENERAL_ERROR;

        // Ldap group. Group code: 1003
        case error::code::COMMON_LDAP:
        case error::code::LDAP_CLIENT_INIT:
        case error::code::LDAP_SEARCH_REQUEST:
        case error::code::LDAP_USER_NOT_FOUND:
            return sql_state::SHY000_GENERAL_ERROR;

        // NodeKeyManagement group. Group code: 1004
        case error::code::KEY_DECODING:
        case error::code::KEY_EXPIRED:
        case error::code::KEY_GENERATION:
        case error::code::KEY_STORE:
        case error::code::KEY_SER_DE:
        case error::code::KEY_VALIDATION:
            return sql_state::SHY000_GENERAL_ERROR;

        // Jwt group. Group code: 1005
        case error::code::JWT_VALIDATION:
        case error::code::JWT_SER_DE:
            return sql_state::SHY000_GENERAL_ERROR;

        // Snapshots group. Group code: 1006
        case error::code::SNAPSHOT:
        case error::code::SNAPSHOT_CANCELED:
        case error::code::SNAPSHOT_ILLEGAL_ARGUMENT:
        case error::code::SNAPSHOT_NOT_FOUND:
        case error::code::SNAPSHOT_META_NOT_FOUND:
        case error::code::SNAPSHOT_OPERATION_NOT_FOUND:
        case error::code::SNAPSHOT_TABLES_NOT_FOUND:
        case error::code::SNAPSHOT_URI_NOT_FOUND:
        case error::code::SNAPSHOT_REPLICA_TIMEOUT:
        case error::code::SNAPSHOT_ENCRYPTION_PROVIDER_NOT_FOUND:
            return sql_state::SHY000_GENERAL_ERROR;

        // DataCenterReplication group. Group code: 1007
        case error::code::DCR:
        case error::code::REPLICATION_CREATE:
        case error::code::REPLICATION_STARTUP:
        case error::code::RUNNING_REPLICATION_REMOVE:
        case error::code::INCOMPATIBLE_SCHEMAS:
        case error::code::REPLICATION_STOP:
        case error::code::SOURCE_TABLE_NOT_EXIST:
        case error::code::REPLICATION_STARTUP_SAME_TABLE:
        case error::code::REPLICATION_NOT_FOUND:
        case error::code::REPLICATION_ALREADY_EXISTS:
        case error::code::SOURCE_TABLES_NOT_DEFINED:
        case error::code::REPLICATION_TO_SELF:
            return sql_state::SHY000_GENERAL_ERROR;

        // Encryption group. Group code: 1008
        case error::code::KEY_PROVIDER_NOT_FOUND:
        case error::code::INVALID_KEY_PROVIDER_CONFIGURATION:
        case error::code::CANNOT_INIT_KEY_PROVIDER:
        case error::code::DATA_ENCRYPTION_KEY_NOT_FOUND:
        case error::code::AWS_KMS_COMMON:
        case error::code::AWS_KMS_KEY_NOT_FOUND:
        case error::code::AWS_KMS_KEY_DISABLED:
            return sql_state::SHY000_GENERAL_ERROR;

        // License group. Group code: 1009
        case error::code::COMMON_LICENSE:
        case error::code::MISSING_LICENSE:
        case error::code::INVALID_SIGNATURE:
        case error::code::MISSING_REQUIRED_FEATURES:
        case error::code::INVALID_BLOCKED_LICENSES_LIST:
            return sql_state::SHY000_GENERAL_ERROR;

        // License group. Group code: 1010
        case error::code::CACHE_STORE_CONFIG:
        case error::code::CACHE_STORE_ACCESS:
            return sql_state::SHY000_GENERAL_ERROR;

        // MemoryQuota group. Group code: 1011
        case error::code::SPILLING:
        case error::code::DISK_QUOTA_EXCEEDED:
        case error::code::STATEMENT_MEMORY_QUOTA_EXCEEDED:
        case error::code::SQL_OUT_OF_MEMORY:
            return sql_state::SHY000_GENERAL_ERROR;

        // Pitr group. Group code: 1012
        case error::code::PITR:
        case error::code::PITR_CANCELED:
            return sql_state::SHY000_GENERAL_ERROR;

        // Cache group. Group code: 1014
        case error::code::TX_INCOMPATIBLE_OPERATION:
            return sql_state::SHY000_GENERAL_ERROR;

        // Secondary storage group. Group code: 1015
        case error::code::SECONDARY_STORAGE_REPLICATION_FAILURE:
        case error::code::SECONDARY_STORAGE_REPLICATION_MANAGER_STARTUP:
        case error::code::SECONDARY_STORAGE_BRIDGE_STARTUP:
        case error::code::SECONDARY_STORAGE_NOT_INITIALIZED:
        case error::code::SECONDARY_STORAGE_WRITE:
        case error::code::SECONDARY_STORAGE_READ:
            return sql_state::SHY000_GENERAL_ERROR;

        // Watermark group. Group code: 1015
        case error::code::WATERMARK_TOO_OLD:
        case error::code::WATERMARK_TOO_OLD_TABLE_DOES_NOT_EXIST:
            return sql_state::SHY000_GENERAL_ERROR;

        // CDC group. Group code: 1016
        case error::code::COMMON_CDC:
        case error::code::CDC_INTERNAL:
        case error::code::CDC_VALIDATION:
        case error::code::CDC_SINK_INIT:
        case error::code::CDC_REPLICATION_START:
        case error::code::CDC_REPLICATION_STOP:
        case error::code::CDC_SINK_ALREADY_EXISTS:
        case error::code::CDC_SOURCE_ALREADY_EXISTS:
        case error::code::CDC_SOURCE_NOT_FOUND:
        case error::code::CDC_SINK_NOT_FOUND:
        case error::code::CDC_REPLICATION_NOT_FOUND:
        case error::code::CDC_REPLICATION_ALREADY_EXISTS:
        case error::code::CDC_DISABLED:
            return sql_state::SHY000_GENERAL_ERROR;
    }

    return sql_state::SHY000_GENERAL_ERROR;
}

sql_state response_status_to_sql_state(int32_t status) {
    switch (response_status(status)) {
        case response_status::PARSING_FAILURE:
        case response_status::KEY_UPDATE:
        case response_status::UNEXPECTED_OPERATION:
            return sql_state::S42000_SYNTAX_ERROR_OR_ACCESS_VIOLATION;

        case response_status::UNSUPPORTED_OPERATION:
            return sql_state::SHYC00_OPTIONAL_FEATURE_NOT_IMPLEMENTED;

        case response_status::UNEXPECTED_ELEMENT_TYPE:
            return sql_state::SHY004_INVALID_SQL_DATA_TYPE;

        case response_status::DUPLICATE_KEY:
        case response_status::NULL_KEY:
        case response_status::NULL_VALUE:
            return sql_state::S23000_INTEGRITY_CONSTRAINT_VIOLATION;

        case response_status::TABLE_NOT_FOUND:
            return sql_state::S42S02_TABLE_OR_VIEW_NOT_FOUND;

        case response_status::INDEX_ALREADY_EXISTS:
            return sql_state::S42S11_INDEX_ALREADY_EXISTS;

        case response_status::INDEX_NOT_FOUND:
            return sql_state::S42S12_INDEX_NOT_FOUND;

        case response_status::TABLE_ALREADY_EXISTS:
            return sql_state::S42S01_TABLE_OR_VIEW_ALREADY_EXISTS;

        case response_status::COLUMN_NOT_FOUND:
            return sql_state::S42S22_COLUMN_NOT_FOUND;

        case response_status::COLUMN_ALREADY_EXISTS:
            return sql_state::S42S21_COLUMN_ALREADY_EXISTS;

        case response_status::TRANSACTION_COMPLETED:
            return sql_state::S25000_INVALID_TRANSACTION_STATE;

        case response_status::TRANSACTION_SERIALIZATION_ERROR:
            return sql_state::S40001_SERIALIZATION_FAILURE;

        case response_status::CACHE_NOT_FOUND:
        case response_status::NULL_TABLE_DESCRIPTOR:
        case response_status::CONVERSION_FAILED:
        case response_status::CONCURRENT_UPDATE:
        case response_status::ENTRY_PROCESSING:
        case response_status::TABLE_DROP_FAILED:
        case response_status::STMT_TYPE_MISMATCH:
        case response_status::UNKNOWN_ERROR:
        default:
            return sql_state::SHY000_GENERAL_ERROR;
    }
}

} // namespace ignite
