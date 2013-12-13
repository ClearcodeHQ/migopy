Migopy - Mongo Migrations for Python
=====================================

Migopy is a simple python library which simply allows You to
setup mongo migrations manager for Your fabfile (see fabfile.org): . After that
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
        MONGO_USER_PASSWORD = # password

    migrations = Migrations.create_task()
    # or for new style tasks:
    # from fabric.api import task
    # migrations = task(Migrations.create_task())

and You are done. Migrations files should be putted in 'mongomigrations'
directory which is at the same level as fabfile.py and names of migrations files
should fulfill default pattern:

    (?P<migr_nr>[0-9]+)_[a-z0-9_]+\\.py

Basic commands:

* `fab migrations` - show unregistered migrations
* `fab migrations:execute` - execute unregistered migrations
* `fab migrations:ignore` - register unregistered migrations without executing them
* `fab migrations:help` - show help about the migopy commands

Additional commands:

* `fab migrations:execute,ex_1_ex.py` - execute specyfic migration
* `fab migrations:rollback,ex_1_ex.py` - rollback specyfic migration (do down() function)
* `fab migrations:ignore,ex_2_ex.py` - ignore specyfic migration


Structure of migration file:

.. code-block:: python

    def up(db):
        db.notes.insert({'content': 'test'})
        pass

    def down(db):
        db.notes.remove({'content': 'test'})


where up() function is executed during fab migrations:execute command, and
down() during fab migrations:rollback. Under db variable pymongo database
object is given (pymongo.database.Database).


Handling different environments
----------------

It's common for Fabric to execute tasks on different environments, for
example You probably would like to do that::

    fab staging migrations
    fab production migrations

Example of fabfile.py:

.. code-block:: python

    import migopy
    import settings # your settings

    is_remote = False

    def staging():
        is_remote = True

    def production():
        is_remote = True

    # Bind your settings with those in Migopy
    class Migrations(migopy.MigrationsManager):
        MONGO_HOST = settings.MONGO_HOST

        @classmethod
        def task_hook(cls, subtask, option):
            if is_remote:
                run(cls.fab_command(subtask, option))
                raise migopy.StopTaskExecution()


    migrations = Migrations.create_task()

In the case above when we want to run migrations on remote machines, under
the hood we have to run for example `fab staging migrations` command by
fabric `run()` method. Migopy is not handling remote mongo connections from
local fabric script so we need to raise `fab migrations` itself on remote
machines.

To do this we have to implement `task_hook()` class method. In the example
task_hook simply recognize if we choose remote environment and if we does it
runs itself by created string command, on remote machine and stop further
execution (to stop raising migopy tasks on local).


More on migration files
----------------

Migration files are quite flexible, if special mongo connection is needed or
better integration with Mongokit You can import mongokit models or pymongo
in migration file directly.

Under the hood Migopy import each migration file as module and
executes up/down functions giving pymongo database object as an argument.

.. code-block:: python

    import mymongokitmodel

    def up(db):
        note = mymongokitmodel.Notes()
        note['name'] = 'test'
        note.save()

in the case above, mongokitmodel handle mongo connection by it's own.

Further customization
----------------

Additional configuration

.. code-block:: python

    class Migrations(migopy.MigrationsManager):
        MIGRATIONS_DIRECTORY = # directory where migrations files will be stored
        MIGRATIONS_FILE_PATTERN = # regex pattern of the migrations files
        DO_MONGO_DUMP = True # will do mongo dump before migrations execution
        MONGO_DUMP_DIRECTORY = # directory where database dump will be stored

For more, check migopy.MigrationsManager class attributes.
You can override selected methods

.. code-block:: python

    class Migrations(migopy.MigrationsManager):
        @migopy.task
        def execute(self, spec_migr=None):
            super(Migrations, self).execute(spec_migr)
            ...

        @migopy.task
        def dbdump(self):
            ...


You can add, additional migrations subtasks

.. code-block:: python

    import migopy

    class Migrations(migopy.MigrationsManager):
        @migopy.task
        def mytask(self, option=None):
            """Here should be a help doc which will be showed under
            fab migrations:help command"""
            pass

::

    fab migrations:mytask
    fab migrations:mytask,some_option



Setup for development
-----------------
::

    $ git clone https://github.com/clearcode/migopy.git
    $ cd migopy
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -e .

Unit tests::

    $ python -m unittest tests.test_units

Integration tests::

    $ python -m unittest tests.test_integrations

All::

    $ python -m unittest discover

