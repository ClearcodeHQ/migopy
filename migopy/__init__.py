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

import datetime
import importlib
import logging
import os
import pymongo
import re
import sys

from contextlib import contextmanager
from fabric.api import local
from fabric.colors import white


class MigopyException(Exception):
    pass


class StopTaskExecution(Exception):
    pass


class Str(str):
    """Add coloring abilities for terminal output
    Usage: Str('something').color(Str.RED)
    """
    RED = '\033[91m'
    GREEN = '\033[92m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    END = '\033[0m'

    def color(self, color_value, bold=False):
        if bold:
            return Str(self.BOLD + color_value + self + self.END)
        return Str(color_value + self + self.END)


@contextmanager
def cwd_in_syspath():
    sys.path.insert(0, os.getcwd())
    yield
    sys.path.pop(0)


def task(method=None, default=False):
    """Decoratorator which marks which methods of migration manager
    will be subtasks of migration fabric task. It only adds 'migopy_task'
    attribute with proper value."""
    if method:
        if default:
            method.migopy_task = 'default'
        else:
            method.migopy_task = True
        return method
    else:
        def wrapper(method):
            if default:
                method.migopy_task = 'default'
            else:
                method.migopy_task = True
            return method
        return wrapper


class ColorsLogger(object):
    "Logger adapter"
    def __init__(self):
        formatter = logging.Formatter('%(message)s')
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        self._logger = logging.getLogger('migopy')
        self._logger.setLevel(logging.DEBUG)
        self._logger.addHandler(handler)

    def white(self, msg):
        self._logger.info(white(msg))

    def red(self, msg):
        self._logger.info(Str(msg).color(Str.RED))

    def green(self, msg):
        self._logger.info(Str(msg).color(Str.GREEN))

    def white_bold(self, msg):
        self._logger.info(white(msg, bold=True))


class MigrationsManager(object):
    MIGRATIONS_FILE_PATTERN = '(?P<migr_nr>[0-9]+)_[a-z0-9_]+\.py'
    MIGRATIONS_COLLECTION = 'migrations'
    MIGRATIONS_DIRECTORY = 'mongomigrations'
    MONGO_HOST = 'localhost'
    MONGO_PORT = 27017
    MONGO_DATABASE = None
    MONGO_USER = None
    MONGO_USER_PASS = None
    MONGO_DUMP_DIRECTORY = 'mongodumps'
    DO_MONGO_DUMP = False
    logger = ColorsLogger()
    MongoClient = pymongo.MongoClient

    def __init__(self):
        self.db = None
        self.collection = None
        if self.MONGO_DATABASE:
            self.mongo_client = self.MongoClient(self.MONGO_HOST,
                                                 self.MONGO_PORT)
            self.db = self.mongo_client[self.MONGO_DATABASE]
            if self.MONGO_USER and self.MONGO_USER_PASS:
                self.db.authenticate(self.MONGO_USER, self.MONGO_USER_PASS)
            self.collection = self.db[self.MIGRATIONS_COLLECTION]

    def sorted(self, migr_files):
        exc_msg = "Founded incorrect name of migration file: %s\n" + \
                  "Script aborted. Required pattern: " + \
                  self.MIGRATIONS_FILE_PATTERN

        if '__init__.py' in migr_files:
            migr_files.remove('__init__.py')

        if len(migr_files) == 1:
            match1 = re.match(self.MIGRATIONS_FILE_PATTERN, migr_files[0])
            if not match1:
                raise MigopyException(exc_msg % migr_files[0])

            return migr_files

        def sort_func(fname1, fname2):
            match1 = re.match(self.MIGRATIONS_FILE_PATTERN, fname1)
            match2 = re.match(self.MIGRATIONS_FILE_PATTERN, fname2)

            if not match1 or not match2:
                raise MigopyException(exc_msg)

            m1_nr = int(match1.group('migr_nr'))
            m2_nr = int(match2.group('migr_nr'))
            return cmp(m1_nr, m2_nr)

        return sorted(migr_files, sort_func)

    def unregistered(self):
        if not os.path.exists(self.MIGRATIONS_DIRECTORY):
            raise MigopyException("Migrations directory %s not founded" %
                                  self.MIGRATIONS_DIRECTORY)

        initpy_path = '%s/__init__.py' % self.MIGRATIONS_DIRECTORY
        if not os.path.exists(initpy_path):
            with open(initpy_path, 'w'):
                pass

        migr_files = [fname for fname in os.listdir(self.MIGRATIONS_DIRECTORY)
                      if re.search('\.py$', fname)]
        migr_files = [filename for filename in migr_files if
                      not self.collection.find_one({'name': filename})]
        return self.sorted(migr_files)

    @task(default=True)
    def show_status(self):
        """Show status of unregistered migrations (default)"""
        unreg_migr = self.unregistered()
        if unreg_migr:
            self.logger.white_bold('Unregistered migrations ' +
                                   '(fab migrations:execute to execute them):')
            for migr in unreg_migr:
                self.logger.red(migr)
        else:
            self.logger.green('All migrations registered, nothing to execute')

    @task
    def execute(self, spec_migr=None):
        """Executes migrations"""
        unreg_migr = self.unregistered()
        if not unreg_migr:
            self.show_status()
            return None

        if spec_migr and spec_migr not in unreg_migr:
            raise MigopyException(('Migration %s is not on unregistred ' +
                                  'migrations list. Can not be executed') %
                                  spec_migr)

        if spec_migr:
            unreg_migr = [spec_migr]

        if self.DO_MONGO_DUMP:
            self.dbdump()

        with cwd_in_syspath():
            for migr in unreg_migr:
                self.logger.white_bold('Executing migration %s...' % migr)
                migr_name = re.sub('\.py$', '', migr)
                module_name = '%s.%s' % (self.MIGRATIONS_DIRECTORY, migr_name)
                migr_mod = importlib.import_module(module_name)
                migr_mod.up(self.db)
                self.collection.insert({'name': migr})

    @task
    def ignore(self, spec_migr=None):
        """Register migrations without executing"""
        unreg_migr = self.unregistered()
        if not unreg_migr:
            self.show_status()
            return None

        if spec_migr and spec_migr not in unreg_migr:
            raise MigopyException(('Migration %s is not on unregistred ' +
                                   'migrations list. Can not be executed') %
                                  spec_migr)

        if spec_migr:
            unreg_migr = [spec_migr]

        for migr in unreg_migr:
            self.logger.white_bold('Registering migration %s...' % migr)
            self.collection.insert({'name': migr})

    @task
    def rollback(self, spec_migr):
        """Rollback specyfic migration"""
        if spec_migr not in self.unregistered():
            raise MigopyException(('Migration %s is not on unregistred ' +
                                   'migrations list. Can not be executed') %
                                  spec_migr)
        spec_migr_name = re.sub('\.py$', '', spec_migr)
        with cwd_in_syspath():
            migr_mod = importlib.import_module('%s.%s' %
                                    (self.MIGRATIONS_DIRECTORY, spec_migr_name))
        self.logger.white_bold('Rollback migration %s...' % spec_migr)
        migr_mod.down(self.db)
        self.collection.remove({'name': spec_migr})

    @task
    def dbdump(self):
        """Do mongo dump"""
        if not self.MONGO_DATABASE:
            raise MigopyException("Name of mongo database not given")

        filename = re.sub('[:\.\s]', '_', str(datetime.datetime.now()))
        path = '%s/%s' % (self.MONGO_DUMP_DIRECTORY, filename)
        command = 'mongodump -d %s -o %s' % (self.MONGO_DATABASE, path)
        if self.MONGO_USER and self.MONGO_USER_PASS:
            command += '-u %s -p %s' % (self.MONGO_USER, self.MONGO_USER_PASS)

        self.logger.white_bold('Doing mongo dump...')
        local(command)

    @staticmethod
    def tasks(migr_mng):
        """It returns all migopy tasks"""
        for attr_name in dir(migr_mng):
            attr = getattr(migr_mng, attr_name)
            if hasattr(attr, 'migopy_task') and (attr.migopy_task == True or
                attr.migopy_task == 'default'):
                yield attr

    @task
    def help(self):
        """Show help for migrations commands"""
        for task in self.tasks(self):
            if hasattr(task, '__doc__') and hasattr(task, '__name__') and \
                task.__doc__ and task.__name__:
                name = task.__name__
                doc = task.__doc__.replace('\n', ' ')
                self.logger.white("fab migrations:%s - %s" %
                                   (name, doc.strip()))

    @classmethod
    def fab_command(cls, subtask=None, option=None):
        command = 'fab migrations'
        if subtask:
            command += ':' + subtask
            if option:
                command += ',' + option
        return command

    @classmethod
    def task_hook(cls, subtask, option):
        pass

    @classmethod
    def create_task(cls):
        def migrations(subtask=None, spec_migr=None):
            """Mongo migrations (migopy)"""
            try:
                cls.task_hook(subtask, spec_migr)
                migrations = cls()
                # migration manager attributes
                for task in cls.tasks(migrations):
                    # not default tasks searching
                    if subtask and subtask == task.__name__:
                        if spec_migr:
                            return task(spec_migr)
                        else:
                            return task()

                    # default task searching
                    if not subtask and task.migopy_task == 'default':
                        if spec_migr:
                            return task(spec_migr)
                        else:
                            return task()
            except StopTaskExecution:
                pass

            except MigopyException as e:
                cls.logger.red(e.message)

        return migrations
