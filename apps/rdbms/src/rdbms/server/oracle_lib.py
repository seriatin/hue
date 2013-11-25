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
  import cx_Oracle as Database
except ImportError, e:
  from django.core.exceptions import ImproperlyConfigured
  raise ImproperlyConfigured("Error loading cx_Oracle module: %s" % e)

from rdbms.server.rdbms_base_lib import BaseRDBMSDataTable, BaseRDBMSResult, BaseRDMSClient


LOG = logging.getLogger(__name__)


class DataTable(BaseRDBMSDataTable): pass


class Result(BaseRDBMSResult): pass


class OracleClient(BaseRDMSClient):
  """Same API as Beeswax"""

  data_table_cls = DataTable
  result_cls = Result

  def __init__(self, *args, **kwargs):
    super(OracleClient, self).__init__(*args, **kwargs)
    self.connection = Database.connect(self._conn_string, **{})


  @property
  def _conn_string(self):
    if self.query_server['server_host']:
      dsn = Database.makedsn(self.query_server['server_host'],
                             int(self.query_server['server_port']),
                             self.query_server['name'])
    else:
      dsn = self.query_server['name']
    return "%s/%s@%s" % (self.query_server['username'],
                         self.query_server['password'], dsn)


  def use(self, database):
    # Oracle credentials are on a per database basis.
    pass


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
    return [self.query_server['name']]


  def get_tables(self, database, table_names=[]):
    cursor = self.connection.cursor()
    cursor.execute("SELECT table_name FROM all_tables")
    self.connection.commit()
    return [row[0] for row in cursor.fetchall()]


  def get_columns(self, database, table):
    cursor = self.connection.cursor()
    cursor.execute("SELECT column_name FROM user_tab_cols WHERE table_name = '%s'" % table)
    self.connection.commit()
    return [row[0] for row in cursor.fetchall()]
