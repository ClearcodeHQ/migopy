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

import os
import pymongo
import re

from fabric.colors import green, white, red


class MigopyException(Exception):
    pass


class MigrationsManager(object):
    MIGRATIONS_FILE_PATTERN = '(?P<migr_nr>[0-9]+)_[a-z0-9_]+\.py'
    MIGRATIONS_COLLECTION = 'migrations'
    MIGRATIONS_DIRECTORY = 'mongomigrations'
    MONGO_HOST = 'localhost'
    MONGO_PORT = 27017
    MONGO_DATABASE = None

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
                      self.collection.find_one({'name': filename})]
        return self.sorted(migr_files)

    def show_status(self):
        green('All migrations registered, nothing to execute')
        if os.path.exists('mongomigrations'):
            white('Unregistered migrations (fab migrations:execute to ' +
                'execute them):')
