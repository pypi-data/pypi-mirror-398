# Copyright (C) GridGain Systems. All Rights Reserved.
# _________        _____ __________________        _____
# __  ____/___________(_)______  /__  ____/______ ____(_)_______
# _  / __  __  ___/__  / _  __  / _  / __  _  __ `/__  / __  __ \
# / /_/ /  _  /    _  /  / /_/ /  / /_/ /  / /_/ / _  /  _  / / /
# \____/   /_/     /_/   \_,__/   \____/   \__,_/  /_/   /_/ /_/
import pygridgain_dbapi
import dbapi20

from tests.util import server_addresses_basic, check_cluster_started, start_cluster, kill_process_tree


class TestPyIgniteDbApi(dbapi20.DatabaseAPI20Test):
    driver = pygridgain_dbapi
    connect_args = ()
    connect_kw_args = {'address': server_addresses_basic}
    lower_func = 'lower'

    prefix = dbapi20.DatabaseAPI20Test.table_prefix
    ddl1 = 'create table %sbooze (name varchar(20) primary key)' % prefix
    ddl2 = 'create table %sbarflys (name varchar(20) primary key, drink varchar(30))' % prefix

    def setUp(self):
        dbapi20.DatabaseAPI20Test.setUp(self)
        self._srv = None
        if not check_cluster_started():
            self._srv = start_cluster()

    def tearDown(self):
        dbapi20.DatabaseAPI20Test.tearDown(self)
        if self._srv:
            kill_process_tree(self._srv.pid)

    def test_callproc(self):
        # Stored procedures are not supported
        pass

    def test_executemany(self):
        pass

    def test_nextset(self):
        # TODO: IGNITE-22743 Implement execution of SQL scripts
        pass

    def test_non_idempotent_close(self):
        # There is no use in raising error on double close.
        pass

    def test_setinputsizes(self):
        # setoutputsize does not do anything currently.
        pass

    def test_setoutputsize(self):
        # setoutputsize does not do anything currently.
        pass
