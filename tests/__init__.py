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