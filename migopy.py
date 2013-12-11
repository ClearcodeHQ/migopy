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

import importlib
import logging
import os
import pymongo
import re

from fabric.colors import green, white, red


class MigopyException(Exception):
    pass


class StopTaskExecution(Exception):
    pass


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
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    def white(self, msg):
        self._logger.info(white(msg))

    def red(self, msg):
        self._logger.info(red(msg))

    def green(self, msg):
        self._logger.info(green(msg))

    def normal(self, msg):
        self._logger.info(msg)


class MigrationsManager(object):
    MIGRATIONS_FILE_PATTERN = '(?P<migr_nr>[0-9]+)_[a-z0-9_]+\.py'
    MIGRATIONS_COLLECTION = 'migrations'
    MIGRATIONS_DIRECTORY = 'mongomigrations'
    MONGO_HOST = 'localhost'
    MONGO_PORT = 27017
    MONGO_DATABASE = None
    logger = ColorsLogger()

    def __init__(self):
        self.db = None
        self.collection = None
        if self.MONGO_DATABASE:
            self.mongo_client = pymongo.MongoClient(self.MONGO_HOST,
                                                    self.MONGO_PORT)
            self.db = self.mongo_client[self.MONGO_DATABASE]
            self.collection = self.db[self.MIGRATIONS_COLLECTION]

    def sorted(self, migr_files):
        exc_msg = "Founded incorrect name of migration file: %s\n" + \
                  "Script aborted. Required pattern: " + \
                  self.MIGRATIONS_FILE_PATTERN

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
        migr_files = [fname for fname in os.listdir(self.MIGRATIONS_DIRECTORY)
                      if re.search('\.py$', fname)]
        migr_files = [filename for filename in migr_files if
                      not self.collection.find_one({'name': filename})]
        return self.sorted(migr_files)

    @task(default=True)
    def show_status(self):
        unreg_migr = self.unregistered()
        if unreg_migr:
            self.logger.white('Unregistered migrations ' +
                              '(fab migrations:execute to execute them):')
            for migr in unreg_migr:
                self.logger.red(migr)
        else:
            self.logger.green('All migrations registered, nothing to execute')

    @task
    def execute(self, spec_migr=None):
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
            self.logger.normal('Executing migration %s...' % migr)
            migr = re.sub('\.py$', '', migr)
            migr_mod = importlib.import_module(migr)
            migr_mod.up(self.db)

    @task
    def ignore(self, spec_migr=None):
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
            self.logger.normal('Registering migration %s...' % migr)
            self.collection.insert({'name': migr})

    @task
    def rollback(self, spec_migr):
        if spec_migr not in self.unregistered():
            raise MigopyException(('Migration %s is not on unregistred ' +
                                   'migrations list. Can not be executed') %
                                  spec_migr)
        spec_migr = re.sub('\.py$', '', spec_migr)
        migr_mod = importlib.import_module(spec_migr)
        self.logger.normal('Rollback migration %s...' % spec_migr)
        migr_mod.down(self.db)

    @classmethod
    def task_hook(cls, subtask, option):
        pass

    @classmethod
    def create_task(cls):
        def task(subtask=None, spec_migr=None):
            try:
                cls.task_hook(subtask, spec_migr)
                migrations = cls()
                # migration manager attributes
                for attr_name in dir(migrations):
                    attr = getattr(migrations, attr_name)
                    # check if is migopy task
                    if hasattr(attr, 'migopy_task'):
                        # not default tasks searching
                        if subtask and subtask == attr_name:
                            if spec_migr:
                                return getattr(migrations, subtask)(spec_migr)
                            else:
                                return getattr(migrations, subtask)()

                        # default task searching
                        if not subtask and getattr(attr, 'migopy_task')\
                                == 'default':
                            if spec_migr:
                                return getattr(migrations, attr_name)(spec_migr)
                            else:
                                return getattr(migrations, attr_name)()
            except StopTaskExecution:
                pass

            except MigopyException as e:
                cls.logger.red(e.message)

        return task
