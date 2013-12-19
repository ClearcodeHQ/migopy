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

import unittest

import migopy
import mock
import os
from tests import TestDirectory, MigrationsCollectionMock


class MongoMigrationsBehavior(unittest.TestCase):
    def setUp(self):
        class MockedMigrationsManager(migopy.MigrationsManager):
            logger = mock.Mock()
            MongoClient = mock.Mock()

        self.MockedMigrationsManager = MockedMigrationsManager
        self.migr_mng = self.MockedMigrationsManager()
        self.migr_mng.collection = mock.Mock()

    def test_it_connects_with_mongo(self):
        class Migrations(migopy.MigrationsManager):
            logger = mock.Mock()
            MongoClient = mock.MagicMock()
            MONGO_HOST = 'mongo_host'
            MONGO_PORT = 11111

        # when database not given
        Migrations()
        self.assertFalse(Migrations.MongoClient.called)

        # when database given
        Migrations.logger.reset_mock()
        Migrations.MongoClient.reset_mock()
        Migrations.MONGO_DATABASE = 'test_db'
        Migrations()
        Migrations.MongoClient.assert_called_once_with('mongo_host', 11111)


        # when user and user password given
        Migrations.logger.reset_mock()
        Migrations.MongoClient.reset_mock()
        Migrations.MONGO_USER = 'mongo_user'
        Migrations.MONGO_USER_PASS = 'mongo_user_pass'
        Migrations()
        Migrations.MongoClient.\
            assert_called_once_with('mongo_user:mongo_user_pass@mongo_host',
                                    11111)

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
                MigrationsCollectionMock(['1_test.py'])
            unregistered = self.migr_mng.unregistered()
            self.assertEqual(unregistered, ['3_test.py', '12_test.py'])

            # when migrations directory is not python module,
            # creates __init__.py
            self.assertTrue(os.path.exists('mongomigrations/__init__.py'))

            # when no migrations directory founded, raise exception
            test_dir.clear()
            with self.assertRaises(migopy.MigopyException) as cm:
                self.migr_mng.unregistered()

            self.assertTrue(cm.exception.message.startswith("Migrations dir"))

    def test_it_prints_status_of_migrations(self):
        # given test directory
        with TestDirectory() as test_dir:
            self.migr_mng.collection = MigrationsCollectionMock()
            test_dir.mkdir('mongomigrations')
            # when no migrations files found, show 'all registered'
            self.migr_mng.show_status()
            self.assertEqual(self.migr_mng.logger.green.call_count, 1,
                             "Not logged with green message")

            # when some files found, check them and show status
            test_dir.touch('mongomigrations/1_test.py')
            test_dir.touch('mongomigrations/002_test.py')

            self.migr_mng.logger.reset_mock()
            self.migr_mng.show_status()
            self.assertEqual(self.migr_mng.logger.white_bold.call_count, 1,
                             "Not logged with white message")
            self.migr_mng.logger.red.\
                assert_has_calls([mock.call('1_test.py'),
                                  mock.call('002_test.py')])

    def test_it_execute_migrations(self):
        with mock.patch('importlib.import_module') as im_mock:
            self.migr_mng.unregistered = mock.Mock(return_value=['1_test.py',
                                                                 '2_test.py'])
            self.migr_mng.db = 'db_object'
            self.migr_mng.execute()
            mdir = self.migr_mng.MIGRATIONS_DIRECTORY
            im_mock.assert_has_calls([mock.call('%s.1_test' % mdir),
                                      mock.call().up('db_object'),
                                      mock.call('%s.2_test' % mdir),
                                      mock.call().up('db_object')])
            self.assertEqual(self.migr_mng.logger.white_bold.call_count, 2,
                             "Executions not logged")

            # and register them as executed
            self.migr_mng.collection.insert \
                .assert_has_calls([mock.call({'name': '1_test.py'}),
                                   mock.call({'name': '2_test.py'})])

            # when given specyfic migration, executes only it
            im_mock.reset_mock()
            self.migr_mng.execute('1_test.py')
            im_mock.assert_has_calls([mock.call('%s.1_test' % mdir),
                                      mock.call().up('db_object')])
            self.assertEqual(im_mock().up.call_count, 1,
                             'More migrations executed')

            # when given specyfic migration which is not found in unregistered
            with self.assertRaises(migopy.MigopyException):
                self.migr_mng.execute('3_test.py')

    def test_it_ignore_migrations(self):
        self.migr_mng.unregistered = mock.Mock(return_value=['1_test.py',
                                                             '2_test.py'])
        self.migr_mng.ignore()
        self.migr_mng.collection.insert\
            .assert_has_calls([mock.call({'name': '1_test.py'}),
                               mock.call({'name': '2_test.py'})])
        self.assertEqual(self.migr_mng.logger.white_bold.call_count, 2,
                         "Ignores not logged")

        # when given specyfic migration, ignores only it
        self.migr_mng.collection.reset_mock()
        self.migr_mng.ignore('1_test.py')
        self.migr_mng.collection.insert \
            .assert_has_calls([mock.call({'name': '1_test.py'})])
        self.assertEqual(self.migr_mng.collection.insert.call_count, 1,
                         'More migrations ignored')

        # when given specyfic migration is not found in unregistered
        with self.assertRaises(migopy.MigopyException):
            self.migr_mng.ignore('3_test.py')

    def test_it_rollback_migration(self):
        with mock.patch('importlib.import_module') as im_mock:
            self.migr_mng.unregistered = mock.Mock(return_value=['1_test.py',
                                                                 '2_test.py'])
            self.migr_mng.db = 'db_object'
            self.migr_mng.rollback('1_test.py')
            mdir = self.migr_mng.MIGRATIONS_DIRECTORY
            im_mock.assert_has_calls([mock.call('%s.1_test' % mdir),
                                      mock.call().down('db_object')])
            self.assertEqual(im_mock().down.call_count, 1,
                             'Executed rollback on more than 1 migrations')
            self.assertEqual(self.migr_mng.logger.white_bold.call_count, 1,
                             "Rollback not logged")

            # and remove migration from register
            self.migr_mng.collection.remove \
                .assert_has_calls([mock.call({'name': '1_test.py'})])

            # when given specyfic migration is not found in unregistered
            with self.assertRaises(migopy.MigopyException):
                self.migr_mng.rollback('3_test.py')

    def test_it_create_task_for_fabfile(self):
        class Migrations(self.MockedMigrationsManager):
            show_status = mock.Mock()
            execute = mock.Mock()
            ignore = mock.Mock()
            rollback = mock.Mock()

        Migrations.show_status.migopy_task = 'default'
        Migrations.show_status.__name__ = 'show_status'
        Migrations.execute.migopy_task = True
        Migrations.execute.__name__ = 'execute'
        Migrations.ignore.migopy_task = True
        Migrations.ignore.__name__ = 'ignore'
        Migrations.rollback.migopy_task = True
        Migrations.rollback.__name__ = 'rollback'
        task = Migrations.create_task()
        self.assertFalse(Migrations.show_status.called)
        self.assertFalse(Migrations.execute.called)
        self.assertFalse(Migrations.ignore.called)
        self.assertFalse(Migrations.rollback.called)
        task()
        Migrations.show_status.assert_called_with()
        task('execute')
        Migrations.execute.assert_called_with()
        task('execute', '1_test.py')
        Migrations.execute.assert_called_with('1_test.py')
        task('ignore')
        Migrations.ignore.assert_called_with()
        task('ignore', '1_test.py')
        Migrations.ignore.assert_called_with('1_test.py')
        task('rollback', '1_test.py')
        Migrations.rollback.assert_called_with('1_test.py')
        self.assertEqual(Migrations.show_status.call_count, 1)
        self.assertEqual(Migrations.execute.call_count, 2)
        self.assertEqual(Migrations.ignore.call_count, 2)
        self.assertEqual(Migrations.rollback.call_count, 1)

    def test_it_allow_to_create_custom_subtasks(self):
        class Migrations(self.MockedMigrationsManager):
            task1_done = False
            task2_done = False

            @migopy.task
            def show_status(self):
                return 'show_status_result'

            @migopy.task
            def task1(self):
                return 'task1_result'

            @migopy.task
            def task2(self):
                return 'task2_result'

            @migopy.task(default=True)
            def task3(self):
                return 'task3_result'

        migr_task = Migrations.create_task()
        self.assertEqual(migr_task('task1'), 'task1_result')
        self.assertEqual(migr_task('task2'), 'task2_result')
        self.assertEqual(migr_task(), 'task3_result')

    def test_it_allow_to_implement_task_hook(self):
        is_remote = True

        class Migrations(self.MockedMigrationsManager):
            show_status = mock.Mock()

            @classmethod
            def task_hook(cls, subtask, option):
                if is_remote:
                    raise migopy.StopTaskExecution()

        Migrations.show_status.migopy_task = 'default'
        task = Migrations.create_task()
        task()
        self.assertFalse(Migrations.show_status.called)

    def test_it_logs_errors_as_red_messages(self):
        class Migrations(self.MockedMigrationsManager):

            @migopy.task(default=True)
            def show_status(self):
                raise migopy.MigopyException("Test message")

        task = Migrations.create_task()
        task()
        Migrations.logger.red.assert_called_once_with("Test message")

    def test_it_shows_help_for_each_migopy_task(self):
        mock_attr = mock.MagicMock()
        mock_attr.__name__ = 'name'
        mock_attr.__doc__ = 'doc'

        class Migrations(self.MockedMigrationsManager):
            task0 = mock_attr

            @migopy.task
            def task1(self):
                "Test doc 1"
                pass

            @migopy.task
            def task2(self):
                """
                Test doc 2
                """
                pass

        migrations = Migrations.create_task()
        migrations('help')
        self.assertTrue(Migrations.logger.white.called, "Help not logger")
        Migrations.logger.white.assert_has_calls(
            [mock.call('fab migrations:task1 - Test doc 1'),
             mock.call('fab migrations:task2 - Test doc 2')])

        # it rejects attributes with dynamic attributes, where they can simulate
        # accidentally migopy_task attribute (like mocks or pymongo objects)
        self.assertFalse(mock.call('fab migrations:name - doc')
            in Migrations.logger.white.mock_calls)

    def test_it_do_mongodump(self):
        with mock.patch('migopy.local') as local_mock:
            # when given only database name
            self.migr_mng.MONGO_DATABASE = 'd'
            self.migr_mng.dbdump()
            self.assertEqual(local_mock.call_count, 1, "local not called")
            call_arg = local_mock.call_args[0][0]
            self.assertTrue(call_arg.startswith('mongodump -d d -o'))
            self.assertEqual(self.migr_mng.logger.white_bold.call_count, 1,
                             "Mongo dump not logged")

            # when given database name, user and password
            self.migr_mng.MONGO_USER = 'u'
            self.migr_mng.MONGO_USER_PASS = 'p'
            self.migr_mng.dbdump()
            self.assertEqual(local_mock.call_count, 2, "local not called")
            call_arg = local_mock.call_args[0][0]
            self.assertTrue(call_arg.startswith('mongodump -d d -o'))
            self.assertTrue(call_arg.endswith('-u u -p p'))
            self.assertEqual(self.migr_mng.logger.white_bold.call_count, 2,
                             "Mongo dump not logged")

    def test_it_optionaly_do_mongodump_before_execution(self):
        with mock.patch('importlib.import_module'):
            self.migr_mng.unregistered = mock.Mock(return_value=['1_test.py'])
            self.migr_mng.dbdump = mock.Mock()
            self.migr_mng.execute()
            self.assertFalse(self.migr_mng.dbdump.called)
            self.migr_mng.DO_MONGO_DUMP = True
            self.migr_mng.execute()
            self.assertTrue(self.migr_mng.dbdump.called)

    def test_it_create_fab_command_from_given_arguments(self):
        self.assertEqual(self.MockedMigrationsManager.fab_command(),
                         'fab migrations')
        self.assertEqual(self.MockedMigrationsManager.fab_command(None),
                         'fab migrations')
        self.assertEqual(self.MockedMigrationsManager.fab_command('task1'),
                         "fab migrations:task1")
        self.assertEqual(self.MockedMigrationsManager.
                         fab_command('task1', 'option1'),
                         "fab migrations:task1,option1")
