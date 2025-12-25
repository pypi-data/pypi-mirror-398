# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
import pytest

import pygridgain_dbapi
from tests.util import server_addresses_invalid, server_addresses_basic


@pytest.mark.parametrize('address', [server_addresses_basic, server_addresses_basic[0]])
def test_connection_success(address):
    conn = pygridgain_dbapi.connect(address=address, timeout=1)
    assert conn is not None
    conn.close()


@pytest.mark.parametrize('address', [server_addresses_basic, server_addresses_basic[0]])
def test_connection_get_cursor(address):
    with pygridgain_dbapi.connect(address=address, timeout=1) as conn:
        assert conn is not None

        cursor = conn.cursor()
        assert cursor.connection is conn
        cursor.close()


@pytest.mark.parametrize('address', [server_addresses_invalid, server_addresses_invalid[0]])
def test_connection_fail(address):
    with pytest.raises(pygridgain_dbapi.OperationalError) as err:
        pygridgain_dbapi.connect(address=address, timeout=1)
    assert err.match('Failed to establish connection with the cluster.')


ERR_MSG_WRONG_TYPE = "Only a string or a list of strings are allowed in 'address' parameter"
ERR_MSG_EMPTY = "No addresses provided to connect"

@pytest.mark.parametrize('address,err_msg', [
    (123, ERR_MSG_WRONG_TYPE),
    ([123], ERR_MSG_WRONG_TYPE),
    ([server_addresses_basic[0], 123], ERR_MSG_WRONG_TYPE),
    ([], ERR_MSG_EMPTY),
    ('', ERR_MSG_EMPTY),
    ([''], ERR_MSG_EMPTY),
])
def test_connection_wrong_arg(address, err_msg):
    with pytest.raises(pygridgain_dbapi.InterfaceError) as err:
        pygridgain_dbapi.connect(address=address, timeout=1)
    assert err.match(err_msg)
