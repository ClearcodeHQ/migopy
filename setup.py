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

from distutils.core import setup

setup(
    name='migopy',
    version='1.0',
    description='Mongo migrations for Python',
    url='https://github.com/clearcode/migopy',
    license='LGPL',
    author='Pawel Galazka',
    author_email='p.galazka@clearcode.cc',
    packages=['migopy'],
    install_requires=[
        'pymongo',
        'fabric',
        'mock'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries'
    ]
)

