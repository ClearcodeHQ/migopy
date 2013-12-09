import migopy
import unittest

class MongoMigrationsIntegratedBehavior(unittest.TestCase):
    def test_it_connects_with_mongo_database(self):
        class Migrations(migopy.MigrationsManager):
            MONGO_DATABASE = 'migo_db_test'

        migr = Migrations()
        migr.db.migo_coll.insert({'name': 'migo_test'})
        self.assertFalse(migr.db.migo_coll.find_one({'name': 'test_migo'}))
        self.assertTrue(migr.db.migo_coll.find_one({'name': 'migo_test'}))
        migr.mongo_client.drop_database(Migrations.MONGO_DATABASE)