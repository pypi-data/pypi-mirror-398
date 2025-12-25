# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
import pytest

import pygridgain_dbapi


def test_non_query(table_name, cursor):
    with pytest.raises(pygridgain_dbapi.ProgrammingError):
        cursor.execute("Non query")


def test_unknown_table(table_name, cursor):
    with pytest.raises(pygridgain_dbapi.ProgrammingError):
        cursor.execute(f"select * from {table_name}")


def test_unknown_column(table_name, cursor, drop_table_cleanup):
    cursor.execute(f'create table {table_name}(id int primary key, data varchar)')
    with pytest.raises(pygridgain_dbapi.ProgrammingError):
        cursor.execute(f"select unknown_col from {table_name}")


def test_unknown_schema(table_name, cursor):
    with pytest.raises(pygridgain_dbapi.ProgrammingError):
        cursor.execute(f'create table UNKNOWN_SCHEMA.{table_name}(id int primary key, data varchar)')


def test_table_exists(table_name, cursor, drop_table_cleanup):
    cursor.execute(f'create table {table_name}(id int primary key, data varchar)')
    with pytest.raises(pygridgain_dbapi.ProgrammingError):
        cursor.execute(f'create table {table_name}(id int primary key, data varchar)')


def test_column_exists(table_name, cursor, drop_table_cleanup):
    cursor.execute(f'create table {table_name}(id int primary key, data varchar)')
    with pytest.raises(pygridgain_dbapi.ProgrammingError):
        cursor.execute(f'alter table {table_name} add data varchar')


def test_cursor_state_fetch(table_name, cursor):
    with pytest.raises(pygridgain_dbapi.InterfaceError):
        cursor.fetchone()


def test_cursor_state_proc(table_name, cursor):
    with pytest.raises(pygridgain_dbapi.NotSupportedError):
        cursor.callproc()


def test_arithmetic_div_by_zero(table_name, cursor):
    with pytest.raises(pygridgain_dbapi.DatabaseError):
        cursor.execute('select 1 / 0')


def test_column_constraints_size(table_name, cursor, drop_table_cleanup):
    cursor.execute(f'create table {table_name}(id int primary key, data varchar(5))')
    with pytest.raises(pygridgain_dbapi.ProgrammingError):
        cursor.execute(f"insert into {table_name} values (1, '1234567890')")


def test_column_constraints_nulls(table_name, cursor, drop_table_cleanup):
    cursor.execute(f'create table {table_name}(id int primary key, data varchar not null)')
    with pytest.raises(pygridgain_dbapi.IntegrityError):
        cursor.execute(f"insert into {table_name} values (1, NULL)")

