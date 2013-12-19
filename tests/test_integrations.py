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
import pymongo.errors
import unittest
from glob import glob
from tests import TestDirectory

files = dict()
files['fabfile.py'] = """
import migopy


class Migrations(migopy.MigrationsManager):
    MONGO_DATABASE = 'migopy_db_test'


migrations = Migrations.create_task()
"""

fabfile_with_task = """
import migopy
from fabric.api import task


class Migrations(migopy.MigrationsManager):
    MONGO_DATABASE = 'migopy_db_test'

migrations = task(Migrations.create_task())

"""

fabfile_with_mongodump = """
import migopy


class Migrations(migopy.MigrationsManager):
    MONGO_DATABASE = 'migopy_db_test'
    DO_MONGO_DUMP = True


migrations = Migrations.create_task()
"""

files['mongomigrations/001_test.py'] = """
def up(db):
    db.test_collection.insert({'test_key': 'test_content'})

def down(db):
    pass
"""

files['mongomigrations/2_test.py'] = """
def up(db):
    pass

def down(db):
    pass
"""


def call(command):
    """Helper for calling shell commands with stdout, stderr handling"""
    proc = subprocess.Popen(command, shell=True,
                            stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    merr = proc.stderr.read()
    print(merr)
    print(proc.stdout.read())
    return merr


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

        # when user data given to connection
        class Migrations(migopy.MigrationsManager):
            MONGO_DATABASE = 'migopy_db_test'
            MONGO_USER = 'migopy'
            MONGO_USER_PASS = 'migopy_pass'

        with self.assertRaises(pymongo.errors.ConfigurationError) as cm:
            Migrations()

        self.assertIn('auth fails', cm.exception.message, cm.exception.message)

    def test_it_do_fab_migrations(self):
        self.migr_mng.collection.insert({'name': '001_test.py'})
        msg = call('fab migrations')
        self.assertIn('2_test.py', msg)
        self.assertNotIn('001_test.py', msg)

    def test_it_do_fab_migrations_execute(self):
        call('fab migrations:execute')
        msg = call('fab migrations')
        self.assertNotIn('001_test.py', msg)
        self.assertNotIn('2_test.py', msg)
        self.assertTrue(self.migr_mng.db.test_collection.find_one(
            {'test_key': 'test_content'}))
        self.assertIn('All migrations', msg)

    def test_it_do_fab_migrations_execute_001_test(self):
        call('fab migrations:execute,001_test.py')
        msg = call('fab migrations')
        self.assertNotIn('001_test.py', msg)
        self.assertIn('2_test.py', msg)

    def test_it_do_fab_migrations_ignore(self):
        call('fab migrations:ignore')
        msg = call('fab migrations')
        self.assertNotIn('001_test.py', msg)
        self.assertNotIn('2_test.py', msg)
        self.assertIn('All migrations', msg)

    def test_it_do_fab_migrations_ignore_001_test(self):
        call('fab migrations:ignore,001_test.py')
        msg = call('fab migrations')
        self.assertNotIn('001_test.py', msg)
        self.assertIn('2_test.py', msg)

    def test_it_do_fab_migrations_dbdump(self):
        self.assertEqual(len(glob('mongodumps/*')), 0)
        call('fab migrations:dbdump')
        self.assertEqual(len(glob('mongodumps/*')), 1)

    def test_it_do_dbdump_during_fab_migrations_execute(self):
        self.assertEqual(len(glob('mongodumps/*')), 0)
        self.tmp_dir.create_file('fabfile.py', fabfile_with_mongodump)
        call('fab migrations:execute')
        self.assertEqual(len(glob('mongodumps/*')), 1)

    def test_it_works_with_fabric_task_decorator(self):
        self.tmp_dir.create_file('fabfile.py', fabfile_with_task)
        msg = call('fab migrations')
        self.assertNotIn('not found', msg, msg)
        self.assertIn('2_test.py', msg)
        self.assertIn('001_test.py', msg)