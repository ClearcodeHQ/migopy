Migopy - Mongo Migrations for Python
=====================================

Migopy is a simple python library which simply allows You to
setup mongo migrations manager for Your fabfile. After that
You will be able to run command like this::

    fab migrations

which returns status of Your migrations, which are registered or not::

    fab migrations:execute

which execute not registered migrations.

Each migration is treated as a seperate python file localized in mongomigrations
directory.

Information which migrations are registered or not is stored in 'migrations'
collection in mongo database.


Quick start
----------------

At first install migopy:

    pip install migopy

then quickly configure mongo migrations in Your fabfile with basic
informations

.. code-block:: python

    import migopy

    class Migrations(migopy.MigrationsManager):
        MONGO_HOST = # host
        MONGO_PORT = # port
        MONGO_USER = # username
        MONGO_PASSWORD = # password

    migrations = Migrations.create_task()

and You are done. Migrations files should be putted in 'mongomigrations'
directory which is at the same level as fabfile.py and names of migrations files
should fulfill default pattern:

    (?P<migr_nr>[0-9]+)_[a-z0-9_]+\.py

Basic commands:

* fab migrations - show unregistered migrations
* fab migrations:execute - execute unregistered migrations
* fab migrations:ignore - register unregistered migrations without executing them
* fab migrations:help - show help about the commands

Additional commands:

* fab migrations:execute,ex_1_ex - execute specyfic migration
* fab migrations:rollback,ex_1_ex - rollback specyfic migration (do down() function)
* fab migrations:ignore,ex_2_ex - ignore specyfic migration


Structure of migration file:

.. code-block:: python

    def up():
        pass

    def down():
        pass

    if __name__ == '__main__':
        up()


where up() function is executed during fab migrations:execute command, and
down() during fab migrations:rollback


Customization
----------------

Additional configuration

.. code-block:: python

    class Migrations(migopy.MigrationsManager):
        MIGRATIONS_DIRECTORY = # directory where migrations files will be stored
        MIGRATIONS_FILE_PATTERN = # regex pattern of the migrations files
        MONGO_DUMP_DIRECTORY = # directory where database dump will be stored

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
            "Here should be a help doc"
            pass

::

    fab migrations:dump

