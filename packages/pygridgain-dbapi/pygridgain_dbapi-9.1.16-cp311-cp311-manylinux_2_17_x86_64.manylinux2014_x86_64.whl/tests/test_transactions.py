# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
import pygridgain_dbapi
from tests.util import server_addresses_basic


def create_tx_test_table(cursor, table_name):
    cursor.execute(f'drop table if exists {table_name}')
    cursor.execute(f'create table {table_name}(id int primary key, val int)')


def test_commit_rollback_setautocommit(table_name, connection, cursor, drop_table_cleanup):
    create_tx_test_table(cursor, table_name)
    assert connection.autocommit is True

    connection.setautocommit(False)
    assert connection.autocommit is False

    cursor.execute(f'insert into {table_name} values (42, 10)')
    connection.commit()

    cursor.execute(f'update {table_name} set val=23 where id=42')
    connection.rollback()

    cursor.execute(f'select val from {table_name} where id=42')
    row = cursor.fetchone()

    assert row[0] == 10


def test_commit_rollback_autocommit_setter(table_name, connection, cursor, drop_table_cleanup):
    create_tx_test_table(cursor, table_name)
    assert connection.autocommit is True

    cursor.execute(f'insert into {table_name} values (42, 10)')

    connection.autocommit = False
    assert connection.autocommit is False

    cursor.execute(f'update {table_name} set val=23 where id=42')
    connection.rollback()

    cursor.execute(f'select val from {table_name} where id=42')
    row = cursor.fetchone()

    assert row[0] == 10


def test_commit_rollback_autocommit_connection(table_name, drop_table_cleanup):
    with pygridgain_dbapi.connect(address=server_addresses_basic, autocommit=True) as conn:
        with conn.cursor() as cursor:
            create_tx_test_table(cursor, table_name)

    with pygridgain_dbapi.connect(address=server_addresses_basic, autocommit=False) as conn_tx:
        assert conn_tx.autocommit is False
        with conn_tx.cursor() as cursor:
            cursor.execute(f'insert into {table_name} values (123, 999)')
            conn_tx.commit()

            cursor.execute(f'update {table_name} set val=777 where id=123')

    with pygridgain_dbapi.connect(address=server_addresses_basic, autocommit=True) as conn:
        assert conn.autocommit is True
        with conn.cursor() as cursor:
            cursor.execute(f'select val from {table_name} where id=123')
            row = cursor.fetchone()
            assert row[0] == 999

