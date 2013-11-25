#!/usr/bin/env python
# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

try:
    import MySQLdb as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading MySQLdb module: %s" % e)

# We want version (1, 2, 1, 'final', 2) or later. We can't just use
# lexicographic ordering in this check because then (1, 2, 1, 'gamma')
# inadvertently passes the version test.
version = Database.version_info
if (version < (1,2,1) or (version[:3] == (1, 2, 1) and
        (len(version) < 5 or version[3] != 'final' or version[4] < 2))):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("MySQLdb-1.2.1p2 or newer is required; you have %s" % Database.__version__)

from rdbms.server.rdbms_base_lib import BaseRDBMSDataTable, BaseRDBMSResult, BaseRDMSClient


LOG = logging.getLogger(__name__)


class DataTable(BaseRDBMSDataTable): pass


class Result(BaseRDBMSResult): pass


class MySQLClient(BaseRDMSClient):
  """Same API as Beeswax"""

  data_table_cls = DataTable
  result_cls = Result

  def __init__(self, *args, **kwargs):
    super(MySQLClient, self).__init__(*args, **kwargs)
    self.connection = Database.connect(**self._conn_params)


  @property
  def _conn_params(self):
    params = {
      'user': self.query_server['username'],
      'passwd': self.query_server['password'],
      'host': self.query_server['server_host'],
      'port': self.query_server['server_port']
    }

    if 'name' in self.query_server:
      params['db'] = self.query_server['name']

    return params


  def use(self, database):
    if 'db' in self._conn_params and self._conn_params['db'] != database:
      raise RuntimeError("Tried to use database %s when %s was specified." % (database, self._conn_params['db']))
    else:
      cursor = self.connection.cursor()
      cursor.execute("USE %s" % database)
      self.connection.commit()


  def execute_statement(self, statement):
    cursor = self.connection.cursor()
    cursor.execute(statement)
    self.connection.commit()
    if cursor.description:
      columns = [column[0] for column in cursor.description]
    else:
      columns = []
    return self.data_table_cls(cursor, columns)


  def get_databases(self):
    cursor = self.connection.cursor()
    cursor.execute("SHOW DATABASES")
    self.connection.commit()
    return [row[0] for row in cursor.fetchall()]


  def get_tables(self, database, table_names=[]):
    cursor = self.connection.cursor()
    cursor.execute("SHOW TABLES")
    self.connection.commit()
    return [row[0] for row in cursor.fetchall()]


  def get_columns(self, database, table):
    cursor = self.connection.cursor()
    cursor.execute("SHOW COLUMNS %s.%s" % (database, table))
    self.connection.commit()
    return [row[0] for row in cursor.fetchall()]
