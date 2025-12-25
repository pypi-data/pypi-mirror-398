# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
import pytest


# TODO: IGNITE-26358: Enable heartbeats in tests and add variant with batch_size 300 and 2000 once heartbeats are implemented
@pytest.mark.parametrize("batch_size", [1, 2, 10])
def test_executemany_success(table_name, cursor, drop_table_cleanup, batch_size):
    test_data = [(i, f'data_{i}') for i in range(batch_size)]

    cursor.execute(f'create table {table_name}(id int primary key, data varchar)')
    cursor.executemany(f"insert into {table_name} values(?, ?)", test_data)
    cursor.execute(f"select id, data from {table_name} order by id")

    for i in range(batch_size):
        row = cursor.fetchone()
        row_expected = test_data[i]
        assert len(row) == len(row_expected)
        assert row == row_expected

    end = cursor.fetchone()
    assert end is None
