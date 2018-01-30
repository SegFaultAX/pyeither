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
    'Either', 'Left', 'Right', 'left', 'failure', 'fail', 'right', 'success',
    'succeed', 'fmap', 'app', 'pure', 'lift', 'bind', 'combine', 'bimap',
    'first', 'second', 'foldr', 'length', 'null', 'traverse', 'sequence',
    'traverseL', 'sequenceL', 'identity', 'join', 'lmap', 'attempt', 'should',
    'predicate', 'kleisli', 'partition_eithers', 'lefts', 'rights', 'is_left',
    'is_right', 'either',
]

@attr.s(frozen=True)
class Either(object):
    """Base type for Either sum type"""

    def fmap(self, f):
        """See: either.fmap"""
        return fmap(f, self)

    def app(self, e2):
        """See: either.app"""
        return app(self, e2)

    def pure(self, v):
        """See: either.pure"""
        return pure(v)

    def bind(self, f):
        """See: either.bind"""
        return bind(self, f)

    def combine(self, e):
        """See: either.combine"""
        return combine(self, e)

    def bimap(self, f, g):
        """See: either.bimap"""
        return bimap(f, g, self)

    def first(self, f):
        """See: either.first"""
        return first(f, self)

    def second(self, g):
        """See: either.second"""
        return second(g, self)

    def traverse(self, f, ev):
        """See: either.traverse"""
        return traverse(f, self.either, ev)

    def sequence(self, ev):
        """See: either.sequence"""
        return sequence(self.either, ev)

    def join(self):
        """See: either.join"""
        return join(self)

    def lmap(self, f):
        """See: either.lmap"""
        return lmap(f, self)

@attr.s(frozen=True)
class Left(Either):
    """Left case for Either sum type"""

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
    """Right case for Either sum type"""

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

failure = left
fail = left

def right(v):
    """Smart constructor for Right"""

    return Right(v)

success = right
succeed = right

def fmap(f, e):
    """Apply a function `f` in Either `e`

    instance Functor (Either e) where
      fmap :: (a -> b) -> Either e a -> Either e b
    """

    if e.is_right:
        return right(f(e.get()))
    else:
        return e

def app(e1, e2):
    """Sequential application in Either

    instance Apply (Either e) where
      app :: (Either e (a -> b)) -> Either e a -> Either e b
    """

    if e1.is_right:
        return fmap(e1.get(), e2)
    else:
        return e1

def pure(v):
    """Lift a normal value into Either

    instance Applicative (Either e) where
      pure :: a -> Either e a
      (<*>) = app
    """

    return right(v)

@attr.s(frozen=True)
class ArgCollect(object):
    """A helper class for collecting variable-length argument lists"""

    fn = attr.ib()
    args = attr.ib(default=attr.Factory(list))

    def __call__(self, arg):
        self.args.append(arg)
        return self

    def apply(self):
        return self.fn(*self.args)

def lift(f):
    """Promote a function to actions

    liftA :: (Applicative f) => (a -> b) -> f a -> f b
    -- Specialized for Either
    liftA :: (a -> b) -> Either e a -> Either e b

    NOTE: Python support variadic functions, so we don't need to supply
    variations for larger arities, eg `liftA2`, `liftA3` etc.
    """

    def lifted(*args):
        init = pure(ArgCollect(f))
        for arg in args:
            init = app(init, arg)
        return fmap(lambda c: c.apply(), init)
    return lifted

def bind(e, f):
    """Sequentially compose monadic actions in Either

    instance Monad (Either e) where
      (>>=) :: Either e a -> (a -> Either e b) -> Either e b
      return = pure
    """

    if e.is_right:
        return f(e.get())
    else:
        return e

def combine(e1, e2):
    """Combine values of Either

    instance Semigroup (Either e a) where
      (<>) :: Either e a -> Either e a -> Either e a
    """

    if e1.is_left:
        return e2
    else:
        return e1

def bimap(f, g, e):
    """fmap over both sides of Either `e`

    instance Bifunctor Either where
      bimap :: (a -> c) -> (b -> d) -> Either a b -> Either c d
    """

    if e.is_right:
        return right(g(e.get()))
    else:
        return left(f(e.get()))

def first(f, e):
    """fmap over the left side of Either `e`

    first :: (Bifunctor f) => (a -> b) -> f a c -> f b c
    -- Specialized for Either
    first :: (a -> b) -> Either a c -> Either b c
    """

    return bimap(f, identity, e)

def second(g, e):
    """fmap over the right side of Either `e`

    second :: (Bifunctor f) => (a -> b) -> f e a -> f e b
    -- Specialized for Either
    second :: (a -> b) -> Either e a -> Either e b
    """

    return bimap(identity, g, e)


def foldr(f, init, e):
    """Right-associative folder over Either

    instance Foldable (Either e) where
      foldr :: (a -> b -> b) -> b -> Either e a -> b
    """

    if e.is_right:
        return f(e.get(), init)
    else:
        return init

def length(e):
    """Length of Either

    length :: (Foldable f) => f a -> Int
    -- Specialized for (Either e)
    length :: Either e a -> Int
    """

    if e.is_right:
        return 1
    else:
        return 0

def null(e):
    """Predicate indicating an empty (left) Either

    null :: (Foldable f) => f a -> Boolean
    -- Specialized for (Either e)
    null :: Either e a -> Boolean
    """

    return e.is_left

def traverse(f, e, ev):
    """Map right-value to action, evaluate the action, and collect the result

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
    """Evaluate right-value action and collect the result

    sequenceA :: (Traversable t, Applicative f) => t (f a) -> f (t a)
    -- Specialized for (Either e)
    sequenceA :: (Applicative f) => Either e (f a) -> f (Either e a)

    NOTE: Must supply evidence for the Applicative in `e`
    Minimal Evidence: ev.pure, ev.fmap
    """

    return traverse(identity, e, ev)

def traverseL(f, l):
    """Traversal for lists of either actions given by `f`

    -- `traverse` specialized for List and Either
    traverse :: (a -> Either e b) -> [a] -> Either e [b]

    NOTE: List traversal is common, but this library does not provide an
    instance of Traversable for lists, so this function is supplied mostly as a
    convenience.
    """

    append = lambda xs, x: xs + [x]
    init = pure([])
    for e in l:
        init = lift(append)(init, f(e))
    return init

def sequenceL(l):
    """Traversal for lists of either actions

    -- `sequence` specialized for List and Either
    sequence :: [Either e a] -> Either e [a]
    """

    return traverseL(identity, l)

def identity(v):
    """Identity

    id :: a -> a
    """

    return v

def join(e):
    """Reduce one level of monadic nesting

    join :: (Monad m) => m (m a) -> m a
    -- Specialized for (Either e)
    join :: Either e (Either e a) -> Either e a
    """

    return bind(e, identity)

def lmap(f, e):
    """Similar to `fmap`, but for left-valued Either

    lmap :: (e -> f) -> Either e a -> Either f a
    """

    if e.is_left:
        return left(f(e.get()))
    else:
        return e

def attempt(f, *args, **kwargs):
    """Run a side-effect, catching any exception in a Left

    attempt :: (() -> b throws e) -> Either e b
    """

    try:
        result = f(*args, **kwargs)
        return right(result)
    except Exception as e:
        return left(e)

def should(b, if_true, if_false):
    """Evaluate predicate `b`, returning a left or right-value

    should :: Boolean -> a -> e -> Either e a
    """

    if b:
        return right(if_true)
    else:
        return left(if_false)

def predicate(f, err):
    """Similar to `should`, but curries f's argument for later application

    predicate :: (a -> Boolean) -> Err -> a -> Either Err a
    """

    def wrapper(v):
        if f(v):
            return right(v)
        else:
            return left(err)
    return wrapper

def kleisli0(f1, f2):
    """Composition for monadic actions

    (>=>) :: (Monad m) => (a -> m b) -> (b -> m c) -> a -> m c
    -- Specialized for (Either e)
    (>=>) :: (a -> Either e b) -> (b -> Either e c) -> a -> Either e c
    """

    def composed(a):
        return bind(f1(a), f2)

    return composed

def kleisli(f1, *fs):
    """Composition for monadic actions

    composeManyM :: (Monad m) => [(_ -> m _)] -> _ -> m _
    """
    return reduce(kleisli0, fs, f1)

def partition_eithers(xs):
    """Partition a list of Eithers into a list of lefts and a list of rights

    partitionEithers :: [Either e a] -> ([e], [a])
    """

    errors, results = [], []
    for e in xs:
        if e.is_right:
            results.append(e.get())
        else:
            errors.append(e.get())
    return errors, results

def lefts(xs):
    """Extract all left-valued Eithers from a list

    lefts :: [Either e a] -> [e]
    """

    return partition_eithers(xs)[0]

def rights(xs):
    """Extract all right-valued Eithers from a list

    rights :: [Either e a] -> [a]
    """

    return partition_eithers(xs)[1]

def is_left(e):
    """Predicate to check for left-valued Either

    isLeft :: Either e a -> Boolean
    """

    return e.is_left

def is_right(e):
    """Predicate to check for right-valued Either

    isRight :: Either e a -> Boolean
    """

    return e.is_right

def either(f, g, e):
    """Case analysis for Either

    either :: (a -> c) -> (b -> c) -> Either a b -> c

    Note: Superficially similar to `bimap`, but does not lift the result back
    into Either
    """

    if e.is_left:
        return f(e.get())
    else:
        return g(e.get())
