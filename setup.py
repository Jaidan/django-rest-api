try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os

path = os.path.abspath(os.path.dirname(__file__))


setup(
    name="django-rest_api",
    version="0.1.0",
    description="Class Based Views with a RESTful twist",
    author='CREO Agency',
    author_email='john@creoagency.com',
    long_description=open('%s/README.rst' % path, 'r').read(),
    py_modules=[
        'rest_api'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Programming Language :: Python :: 2',
    ],
    install_requires=[
        'django>=1.3'
        'oauth2app>=0.3.0',
    ],
)
