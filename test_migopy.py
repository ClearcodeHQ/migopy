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
import mock
import shutil
import os
import unittest


class TestDirectory(object):
    TMP_DIR_NAME = 'migopy_tmp'

    def __enter__(self):
        self.org_dir = os.getcwd()
        os.mkdir(self.TMP_DIR_NAME)
        os.chdir(self.TMP_DIR_NAME)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.org_dir)
        shutil.rmtree(self.TMP_DIR_NAME)

    def clear(self):
        os.chdir(self.org_dir)
        shutil.rmtree(self.TMP_DIR_NAME)
        os.mkdir(self.TMP_DIR_NAME)
        os.chdir(self.TMP_DIR_NAME)

    def touch(self, path):
        with open(path, 'w'):
            pass

    def mkdir(self, path):
        os.makedirs(path)


class MigrationsCollectionMock(object):
    """
    Very simple mongo db mock, with very narrow query handling. For migopy
    needs. Is simulates collection for registering migrations.
    Example of use:

        migrations = MigrationsCollectionMock(['test1.py', 'test2.py'])

        migrations.find_one({'name': 'test1'})
    """
    def __init__(self, filenames):
        self._db = []
        for fname in filenames:
            self._db.append({'name': fname})

    def find_one(self, dict_query):
        for row in self._db:
            if dict_query['name'] == row['name']:
                return row


class MongoMigrationsBehavior(unittest.TestCase):
    def setUp(self):
        self.migr_mng = migopy.MigrationsManager()

    def test_it_sorts_migration_files(self):
        migrations = ['3_abc.py', '1_abc_cde.py', '2_abc.py']
        sorted = self.migr_mng.sorted(migrations)
        self.assertEqual(sorted, ['1_abc_cde.py', '2_abc.py', '3_abc.py'])

        # when wrong filenames, raise exception
        migrations = ['test_1.py', '001_abc.py']
        with self.assertRaises(migopy.MigopyException) as cm:
            self.migr_mng.sorted(migrations)

        self.assertTrue(cm.exception.message.startswith('Founded'))

        # when only one filename given, check correct name too
        with self.assertRaises(migopy.MigopyException):
            self.migr_mng.sorted(['abc_abc.py'])

    def test_it_returns_unregistered_migrations_in_order(self):
        with TestDirectory() as test_dir:
            test_dir.mkdir('mongomigrations')
            test_dir.touch('mongomigrations/1_test.py')
            test_dir.touch('mongomigrations/12_test.py')
            test_dir.touch('mongomigrations/3_test.py')
            self.migr_mng.collection = \
                MigrationsCollectionMock(['12_test.py', '3_test.py'])
            unregistered = self.migr_mng.unregistered()
            self.assertEqual(unregistered, ['3_test.py', '12_test.py'])

            # when no migrations directory founded, raise exception
            test_dir.clear()
            with self.assertRaises(migopy.MigopyException) as cm:
                self.migr_mng.unregistered()

            self.assertTrue(cm.exception.message.startswith("Migrations dir"))

    def test_it_prints_status_of_migrations(self):
        # given test directory
        with TestDirectory() as test_dir:
            # when no migrations files found, show 'all registered'
            with mock.patch('migopy.green') as green_mock:
                self.migr_mng.show_status()
                green_mock.assert_called_once_with(
                    'All migrations registered, nothing to execute')

            # when some files found, check them and show status
            test_dir.mkdir('mongomigrations')
            test_dir.touch('mongomigrations/1_test.py')
            test_dir.touch('mongomigrations/002_test.py')

            with mock.patch('migopy.white') as white_mock:
                self.migr_mng.show_status()
                white_mock.assert_called_once_with(
                    'Unregistered migrations (fab migrations:execute to ' +
                    'execute them):'
                )

            #with mock.patch('migopy.red') as red_mock:
            #    self.migr_mng.show_status()
            #    red_mock.assert_called_with('1_test.py')
            #    red_mock.assert_called_with('002_test.py')

    def test_it_execute_migrations(self):
        pass

    def test_it_ignore_migrations(self):
        pass

    def test_it_rollback_migration(self):
        pass

    def test_it_allow_basic_configuration(self):
        pass
