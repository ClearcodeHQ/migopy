#Copyright (C) 2013-2014 by Clearcode <http://clearcode.cc>
#and associates (see AUTHORS).
#
#This file is part of migopy.
#
#Migopy is free software: you can redistribute it and/or modify
#it under the terms of the GNU Lesser General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Migopy is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public License
#along with migopy.  If not, see <http://www.gnu.org/licenses/>.

import migopy
import subprocess
import unittest
from tests import TestDirectory

files = dict()
files['fabfile.py'] = """
import migopy


class Migrations(migopy.MigrationsManager):
    MONGO_DATABASE = 'migopy_db_test'


migrations = Migrations.create_task()
"""

files['mongomigrations/001_test.py'] = """
def up(db):
    pass

def down(db):
    pass
"""

files['mongomigrations/2_test.py'] = """
def up(db):
    pass

def down(db):
    pass
"""


class MongoMigrationsIntegratedBehavior(unittest.TestCase):
    def setUp(self):
        class Migrations(migopy.MigrationsManager):
            MONGO_DATABASE = 'migopy_db_test'

        self.Migrations = Migrations
        self.migr_mng = Migrations()
        self.tmp_dir = TestDirectory()
        self.tmp_dir.__enter__()
        self.tmp_dir.mkdir('mongomigrations')
        for path in files:
            self.tmp_dir.create_file(path, files[path])

    def tearDown(self):
        self.migr_mng.mongo_client.drop_database(self.migr_mng.MONGO_DATABASE)
        self.tmp_dir.__exit__(None, None, None)

    def test_it_connects_with_mongo_database(self):
        self.migr_mng.db.migo_coll.insert({'name': 'migo_test'})
        self.assertFalse(
            self.migr_mng.db.migo_coll.find_one({'name': 'test_migo'}))
        self.assertTrue(
            self.migr_mng.db.migo_coll.find_one({'name': 'migo_test'}))

    def test_it_do_fab_migrations(self):
        subprocess.check_call('fab migrations', shell=True)

    def test_id_do_fab_migrations_execute(self):
        pass

    def test_it_do_fab_migrations_ignore(self):
        pass

    def test_it_do_fab_migrations_dbdump(self):
        pass