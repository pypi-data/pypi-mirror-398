# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
import pygridgain_dbapi


def test_execute_const_sql_success(cursor):
    cursor.execute("select 1, 'Lorem Ipsum'")
    assert cursor.rowcount == -1

    assert cursor.description is not None
    assert len(cursor.description) == 2

    assert cursor.description[0].name == '1'
    assert cursor.description[0].type_code == pygridgain_dbapi.INT
    assert cursor.description[0].null_ok is False

    assert cursor.description[1].name == "'Lorem Ipsum'"
    assert cursor.description[1].type_code == pygridgain_dbapi.STRING
    assert cursor.description[1].null_ok is False


def test_execute_sql_table_success(table_name, cursor, drop_table_cleanup):
    cursor.execute(f'create table {table_name}(id int primary key, data varchar, dec decimal(3,5))')
    cursor.execute(f"select id, data, dec from {table_name}")

    assert cursor.description is not None
    assert len(cursor.description) == 3

    assert cursor.description[0].name == 'ID'
    assert cursor.description[0].type_code == pygridgain_dbapi.INT
    assert cursor.description[0].null_ok is False

    assert cursor.description[1].name == 'DATA'
    assert cursor.description[1].type_code == pygridgain_dbapi.STRING
    assert cursor.description[1].null_ok is True

    assert cursor.description[2].name == 'DEC'
    assert cursor.description[2].type_code == pygridgain_dbapi.NUMBER
    assert cursor.description[2].null_ok is True
    assert cursor.description[2].scale == 5
    assert cursor.description[2].precision == 3


def test_execute_update_rowcount(table_name, cursor, drop_table_cleanup):
    cursor.execute(f'create table {table_name}(id int primary key, data varchar)')
    for key in range(10):
        cursor.execute(f"insert into {table_name} values({key}, 'data-{key*2}')")
        assert cursor.rowcount == 1

    cursor.execute(f"update {table_name} set data='Lorem ipsum' where id > 3")
    assert cursor.rowcount == 6
