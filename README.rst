Migopy - Mongo Migrations for Python
=====================================

Migopy is a simple python library which simply allows You to
setup mongo migrations manager for Your fabfile. After that
You will be able to run command like this

.. code-block:: python

    fab migrations

which returns status of Your migrations, which are registered or not

    fab migrations:execute

which execute not registered migrations.

Each migration is treated as a seperate python file localized in mongomigrations
directory.

Information which migrations are registered or not is stored in 'migrations'
collection in mongo database.


Quick start
----------------

In Your fabfile

.. code-block:: python

    import migopy

    class Migrations(migopy.MigrationsManager):
        MONGO_HOST
        MONGO_PORT
        MONGO_USER
        MONGO_PASSWORD

    migrations = Migrations.create_task()


fab staging migrations:execute
fab staging migrations:ignore
fab staging migrations:help


Customization
----------------

Additional configuration

.. code-block:: python

    class Migrations(migopy.MigrationsManager):
        MIGRATIONS_DIRECTORY
        MIGRATIONS_FILE_PATTERN
        MONGO_DUMP_DIRECTORY


You can override selected methods

.. code-block:: python

    class Migrations(migopy.MigrationsManager):
        def do_dump(self):
            pass


You can add, additional migrations subtask

.. code-block:: python

    import migopy


    class Migrations(migopy.MigrationsManager):
        @migopy.task
        def dump(self):
            "Here should be help doc"
            pass


    fab migrations:dump



Migration file
---------------
.. code-block:: python

    def up():
        pass


    def down():
        pass


    if __name__ == '__main__':
        up()
