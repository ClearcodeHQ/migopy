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

"""
Helpers for testing
"""
import shutil
import os


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

    def create_file(self, path, content):
        with open(path, 'w') as f:
            f.write(content)


class MigrationsCollectionMock(object):
    """
    Very simple mongo db mock, with very narrow query handling. For migopy
    needs. Is simulates collection for registering migrations.
    Example of use:

        migrations = MigrationsCollectionMock(['test1.py', 'test2.py'])

        migrations.find_one({'name': 'test1'})
    """
    def __init__(self, filenames = []):
        self._db = []
        for fname in filenames:
            self._db.append({'name': fname})

    def find_one(self, dict_query):
        for row in self._db:
            if dict_query['name'] == row['name']:
                return row