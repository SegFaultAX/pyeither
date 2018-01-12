#!/usr/bin/env python

# The MIT License (MIT)
# Copyright (c) 2018 Michael-Keith Bernard
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""An implementation of `data Either e a = Left e | Right a` in Python"""

import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    from functools import reduce

import attr

__author__ = "Michael-Keith Bernard"
__all__ = [
    'Either', 'Left', 'Right', 'left', 'right', 'fmap', 'app', 'pure', 'bind',
    'combine', 'bimap', 'foldr', 'length', 'null', 'traverse', 'sequence',
    'identity', 'join', 'lmap', 'attempt', 'should', 'predicate', 'kleisli',
    'partition_eithers', 'EitherChain', 'chain', 'unchain',
]

@attr.s(frozen=True)
class Either(object):
    def chained(self):
        return chain(self)

@attr.s(frozen=True)
class Left(Either):
    error = attr.ib()

    def get(self):
        return self.error

    @property
    def is_left(self):
        return True
    @property
    def is_right(self):
        return False

@attr.s(frozen=True)
class Right(Either):
    result = attr.ib()

    def get(self):
        return self.result

    @property
    def is_left(self):
        return False
    @property
    def is_right(self):
        return True

def left(v):
    """Smart constructor for Left"""

    return Left(v)

def right(v):
    """Smart constructor for Right"""

    return Right(v)

def fmap(f, e):
    """
    instance Functor (Either e) where
      fmap :: (a -> b) -> Either e a -> Either e b
    """

    if e.is_right:
        return right(f(e.get()))
    else:
        return e

def app(e1, e2):
    """
    instance Apply (Either e) where
      app :: (Either e (a -> b)) -> Either e a -> Either e b
    """

    if e1.is_right:
        return fmap(e1.get(), e2)
    else:
        return e1

def pure(v):
    """
    instance Applicative (Either e) where
      pure :: a -> Either e a
      (<*>) = app
    """

    return right(v)

def bind(e, f):
    """
    instance Monad (Either e) where
      (>>=) :: Either e a -> (a -> Either e b) -> Either e b
      return = pure
    """

    if e.is_right:
        return f(e.get())
    else:
        return e

def combine(e1, e2):
    """
    instance Semigroup (Either e a) where
      (<>) :: Either e a -> Either e a -> Either e a
    """

    if e1.is_left:
        return e2
    else:
        return e1

def bimap(f, g, e):
    """
    instance Bifunctor Either where
      bimap :: (a -> c) -> (b -> d) -> Either a b -> Either c d
    """

    if e.is_right:
        return right(g(e.get()))
    else:
        return left(f(e.get()))

def foldr(f, init, e):
    """
    instance Foldable (Either e) where
      foldr :: (a -> b -> b) -> b -> Either e a -> b
    """

    if e.is_right:
        return f(e.get(), init)
    else:
        return init

def length(e):
    """
    length :: (Foldable f) => f a -> Int
    -- Specialized for (Either e)
    length :: Either e a -> Int
    """

    if e.is_right:
        return 1
    else:
        return 0

def null(e):
    """
    null :: (Foldable f) => f a -> Boolean
    -- Specialized for (Either e)
    null :: Either e a -> Boolean
    """

    return e.is_left

def traverse(f, e, ev):
    """
    instance Traversable (Either e) where
      traverse :: (Applicative f) => (a -> f b) -> Either e a -> f (Either e b)

    NOTE: Must supply evidence for the Applicative result of `f`
    Minimal Evidence: ev.pure, ev.fmap
    """

    if e.is_right:
        return ev.fmap(right, f(e.get()))
    else:
        return ev.pure(e)

def sequence(e, ev):
    """
    sequenceA :: (Traversable t, Applicative f) => t (f a) -> f (t a)
    -- Specialized for (Either e)
    sequenceA :: (Applicative f) => Either e (f a) -> f (Either e a)

    NOTE: Must supply evidence for the Applicative in `e`
    Minimal Evidence: ev.pure, ev.fmap
    """

    return traverse(identity, e, ev)

def identity(v):
    """
    id :: a -> a
    """

    return v

def join(e):
    """
    join :: (Monad m) => m (m a) -> m a
    -- Specialized for (Either e)
    join :: Either e (Either e a) -> Either e a
    """

    return bind(e, identity)

def lmap(f, e):
    """
    lmap :: (e -> f) -> Either e a -> Either f a
    """

    if e.is_left:
        return left(f(e.get()))
    else:
        return e

def attempt(f, *args, **kwargs):
    """
    attempt :: (() -> b throws e) -> Either e b
    """

    try:
        result = f(*args, **kwargs)
        return right(result)
    except Exception as e:
        return left(e)

def should(b, if_true, if_false):
    """
    should :: Boolean -> a -> e -> Either e a
    """

    if b:
        return right(if_true)
    else:
        return left(if_false)

def predicate(f, err):
    """
    predicate :: (a -> Boolean) -> Err -> a -> Either Err a
    """

    def wrapper(v):
        if f(v):
            return right(v)
        else:
            return left(err)
    return wrapper

def kleisli0(f1, f2):
    """Kleisli composition
    (>=>) :: (Monad m) => (a -> m b) -> (b -> m c) -> a -> m c
    -- Specialized for (Either e)
    (>=>) :: (a -> Either e b) -> (b -> Either e c) -> a -> Either e c
    """

    def composed(a):
        return bind(f1(a), f2)

    return composed

def kleisli(f1, *fs):
    """Kleisli composition over many actions
    composeManyM :: (Monad m) => [(_ -> m _)] -> _ -> m _
    """
    return reduce(kleisli0, fs, f1)

def partition_eithers(xs):
    """
    partitionEithers :: [Either e a] -> ([e], [a])
    """

    errors, results = [], []
    for e in xs:
        if e.is_right:
            results.append(e.get())
        else:
            errors.append(e.get())
    return errors, results

class EitherChain(object):
    def __init__(self, e):
        self.either = e
    def fmap(self, f):
        return EitherChain(fmap(f, self.either))
    def app(self, e2):
        return EitherChain(app(self.either, e2))
    def pure(self, v):
        return EitherChain(pure(v))
    def bind(self, f):
        return EitherChain(bind(self.either, f))
    def combine(self, e):
        return EitherChain(combine(self.either, e))
    def bimap(self, f, g):
        return EitherChain(bimap(f, g, self.either))
    def traverse(self, f, ev):
        return traverse(f, self.either, ev)
    def sequence(self, ev):
        return sequence(self.either, ev)
    def join(self):
        return EitherChain(join(self.either))
    def lmap(self, f):
        return EitherChain(lmap(f, self.either))
    def unchain(self):
        return self.either

def chain(e):
    return EitherChain(e)

def unchain(e):
    return e.unchain()

