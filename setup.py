#!/usr/bin/env python

from setuptools import setup

if __name__ == "__main__":
    setup(
        name='pyeither',
        version='0.1.1',
        packages=['either',],
        license='MIT',
        description='An implementation of Data.Either from Haskell in Python',
        long_description=open('README.md').read(),
        url='https://github.com/segfaultax/pyeither',
        author='Michael-Keith Bernard',
        author_email='mkbernard.dev@gmail.com',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
        ],
        keywords='either haskell data.either monad applicative functor',
        install_requires=[
            'attrs'
        ],
    )
