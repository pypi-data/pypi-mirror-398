# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
import logging

import pygridgain_dbapi
import pytest

from tests.util import check_cluster_started, start_cluster_gen, server_addresses_basic

logger = logging.getLogger('pygridgain_dbapi')
logger.setLevel(logging.DEBUG)

TEST_PAGE_SIZE = 32

@pytest.fixture()
def table_name(request):
    return request.node.originalname


@pytest.fixture()
def connection():
    conn = pygridgain_dbapi.connect(address=server_addresses_basic, page_size=TEST_PAGE_SIZE)
    yield conn
    conn.close()


@pytest.fixture()
def cursor(connection):
    cursor = connection.cursor()
    yield cursor
    cursor.close()


@pytest.fixture()
def drop_table_cleanup(cursor, table_name):
    yield None
    cursor.connection.setautocommit(True)
    cursor.execute(f'drop table if exists {table_name}')


@pytest.fixture(autouse=True, scope="session")
def cluster():
    if not check_cluster_started():
        yield from start_cluster_gen()
    else:
        yield None

