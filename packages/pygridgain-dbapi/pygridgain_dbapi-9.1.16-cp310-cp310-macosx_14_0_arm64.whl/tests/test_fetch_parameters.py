# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
import decimal

import pygridgain_dbapi
import pytest

test_data = [
    0,
    1,
    -1,
    2,
    43,
    -543656,
    423538409739,
    0.0,
    123.456,
    -76.4,
    4235384097394235384097394235384097394235.38409739423538409739423538409739423538409739,
    1.0E-40,
    1.0E40,
    'test',
    'TEST',
    'Lorem Ipsum',
    '你好',
    'Мир!',
    '',
    True,
    False,
    None,
    b'',
    b'0',
    b'123456789',
    b'h9832y9r8wf08hw85h0h2508h0858',
    b'\x45\xf0\xab',
    pygridgain_dbapi.Binary('Lorem Ipsum'),
    pygridgain_dbapi.Binary('x' * 1234),
    pygridgain_dbapi.UUID('c4a0327c-44be-416d-ae90-75c05079789f'),
    pygridgain_dbapi.UUID('00000000-0000-0000-0000-000000000001'),
    pygridgain_dbapi.UUID('10101010-1010-1010-1010-101010101010'),
    pygridgain_dbapi.UUID(int=0),
    pygridgain_dbapi.Time(23, 59, 59),
    pygridgain_dbapi.Time(20, 17, 40),
    pygridgain_dbapi.Time(7, 59, 13),
    pygridgain_dbapi.TIME(1, 2, 3),
    pygridgain_dbapi.TIME(0, 0, 0),
    pygridgain_dbapi.TimeFromTicks(0),
    pygridgain_dbapi.TimeFromTicks(89565),
    pygridgain_dbapi.Date(1969, 7, 20),
    pygridgain_dbapi.Date(1525, 1, 1),
    pygridgain_dbapi.DATE(2024, 9, 12),
    pygridgain_dbapi.DateFromTicks(0),
    pygridgain_dbapi.DateFromTicks(8956872365),
    pygridgain_dbapi.DATETIME(1969, 7, 20, 20, 17, 40),
    pygridgain_dbapi.DATETIME(2024, 9, 12, 7, 59, 13),
    pygridgain_dbapi.DATETIME(1000, 1, 1, 0, 0, 0),
    pygridgain_dbapi.DATETIME(1000, 1, 1, 0, 0, 0),
    pygridgain_dbapi.Timestamp(1979, 7, 20, 20, 17, 40),
    pygridgain_dbapi.Timestamp(2024, 9, 12, 7, 59, 13),
    pygridgain_dbapi.Timestamp(3000, 1, 1, 0, 0, 0),
    pygridgain_dbapi.Timestamp(2007, 1, 1, 0, 0, 0),
    pygridgain_dbapi.TimestampFromTicks(4239085792.333),
    # TODO: IGNITE-17373 Fix DURATION type parameters in select statements
    # pygridgain_dbapi.DURATION(days=0),
    # pygridgain_dbapi.DURATION(days=1),
    # pygridgain_dbapi.DURATION(days=145),
    # pygridgain_dbapi.DURATION(seconds=123456789),
    # pygridgain_dbapi.DURATION(seconds=987654321, milliseconds=123),
    # pygridgain_dbapi.DURATION(days=145, seconds=987654321, milliseconds=123),
]


def check_fetch_parameters(cursor, param, use_tuple: bool):
    cursor.execute("select ?", (param,) if use_tuple else [param])
    data = cursor.fetchone()
    assert len(data) == 1
    if isinstance(param, float):
        assert data[0] == pytest.approx(param)
    else:
        assert data[0] == param


@pytest.mark.parametrize("param", test_data)
def test_fetch_parameter_list(cursor, param):
    check_fetch_parameters(cursor, param, False)


@pytest.mark.parametrize("param", test_data)
def test_fetch_parameter_tuple(cursor, param):
    check_fetch_parameters(cursor, param, True)


test_decs = [
    pygridgain_dbapi.NUMBER('1111111111111111111111111111111'),
    pygridgain_dbapi.NUMBER('11111111111111.11111111111111111'),
    pygridgain_dbapi.NUMBER('0.000000000000000000000000000001'),
    pygridgain_dbapi.NUMBER('123.456789'),
    pygridgain_dbapi.NUMBER('-123.456789'),
    pygridgain_dbapi.NUMBER('2980949468541866002980035546865281241479836693504'),
    pygridgain_dbapi.NUMBER('2980949468541866002980035546865281241479836693504.943353696379651248255943353696379651248255'),
    pygridgain_dbapi.NUMBER('298094946854186600298003554686528124147.9836693504943353696379651248255'),
    pygridgain_dbapi.NUMBER('298094946854186600298003554686528.1241479836693504943353696379651248255'),
    pygridgain_dbapi.NUMBER('29809494685418660029800.35546865281241479836693504943353696379651248255'),
]


def check_fetch_decimals(cursor, param: decimal.Decimal, use_tuple: bool):
    cursor.execute(f"select ?::DECIMAL(100,50)", (param,) if use_tuple else [param])
    data = cursor.fetchone()
    assert len(data) == 1
    if isinstance(param, float):
        assert data[0] == pytest.approx(param)
    else:
        assert data[0] == param


@pytest.mark.parametrize("param", test_decs)
def test_fetch_decimals_list(cursor, param):
    check_fetch_decimals(cursor, param, False)


@pytest.mark.parametrize("param", test_decs)
def test_fetch_decimals_tuple(cursor, param):
    check_fetch_decimals(cursor, param, True)
