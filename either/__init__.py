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

import attr

__author__ = "Michael-Keith Bernard"

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

def partiton_eithers(xs):
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

if __name__ == "__main__":
    import unittest

    @attr.s(frozen=True)
    class Id(object):
        """Identity Monad"""
        v = attr.ib()
        @classmethod
        def fmap(cls, f, i):
            return Id(f(i.v))
        @classmethod
        def app(cls, i1, i2):
            return cls.fmap(i1.v, i2)
        @classmethod
        def pure(cls, v):
            return Id(v)
        @classmethod
        def bind(cls, i, f):
            return f(i.v)

    class EitherTest(unittest.TestCase):
        def test_left(self):
            self.assertEquals(Left("foo").get(), "foo")
            self.assertEquals(left("foo").get(), "foo")

        def test_right(self):
            self.assertEquals(Right("foo").get(), "foo")
            self.assertEquals(right("foo").get(), "foo")

        def test_fmap(self):
            self.assertEquals(fmap(lambda e: e + 1, right(1)), right(2))
            self.assertEquals(fmap(lambda e: e + 1, left("err")), left("err"))

        def test_app(self):
            self.assertEquals(app(right(lambda e: e + 1), right(1)), right(2))
            self.assertEquals(app(right(lambda e: e + 1), left("err")), left("err"))
            self.assertEquals(app(left("err1"), left("err2")), left("err1"))

        def test_pure(self):
            self.assertEquals(pure(1), right(1))

        def test_bind(self):
            self.assertEquals(bind(pure(1), lambda e: right(e + 1)), right(2))
            self.assertEquals(bind(left("err"), lambda e: right(e + 1)), left("err"))

        def test_combine(self):
            self.assertEquals(combine(pure(1), pure(2)), pure(1))
            self.assertEquals(combine(left("err"), pure(2)), pure(2))
            self.assertEquals(combine(left("err"), left("err!")), left("err!"))

        def test_bimap(self):
            lf = lambda e: e + "!"
            rf = lambda e: e + 1
            self.assertEquals(bimap(lf, rf, right(1)), right(2))
            self.assertEquals(bimap(lf, rf, left("err")), left("err!"))

        def test_foldr(self):
            self.assertEquals(foldr(lambda e, v: e / v, 2, pure(10)), 5)
            self.assertEquals(foldr(lambda e, v: e / v, 2, left("err")), 2)

        def test_traverse(self):
            self.assertEquals(traverse(lambda e: Id(e * 2), pure(5), Id), Id(pure(10)))
            self.assertEquals(traverse(lambda e: Id(e * 2), left("err"), Id), Id(left("err")))

        def test_sequence(self):
            self.assertEquals(sequence(pure(Id(1)), Id), Id(pure(1)))
            self.assertEquals(sequence(left("err"), Id), Id(left("err")))

        def test_join(self):
            self.assertEquals(join(pure(pure(5))), pure(5))

        def test_lmap(self):
            self.assertEquals(lmap(lambda e: e + "!", right(1)), right(1))
            self.assertEquals(lmap(lambda e: e + "!", left("err")), left("err!"))

        def test_attempt(self):
            def angry():
                raise RuntimeError("so angry")
            self.assertTrue(attempt(angry).is_left)
            self.assertEquals(attempt(angry).get().message, "so angry")
            self.assertEquals(attempt(lambda e: e, 5), pure(5))

        def test_should(self):
            self.assertEquals(should(True, 1, "err"), pure(1))
            self.assertEquals(should(False, 1, "err"), left("err"))

        def test_predicate(self):
            self.assertEquals(predicate(lambda e: True, "err")(1), pure(1))
            self.assertEquals(predicate(lambda e: False, "err")(1), left("err"))

        def test_chain(self):
            c1 = chain(pure(1)).fmap(lambda e: e + 1).bind(lambda e: pure(e * 2))
            self.assertEquals(c1.unchain(), right(4))

            c2 = chain(pure(1)).bind(lambda _: left("err")).lmap(lambda e: e + "!")
            self.assertEquals(c2.unchain(), left("err!"))

            lf = lambda e: e + "!"
            rf = lambda e: e * 10
            c3 = chain(pure(lambda e: e + 1)).app(pure(1)).bimap(lf, rf)
            self.assertEquals(c3.unchain(), right(20))

        def test_kleisli(self):
            f1 = lambda e: pure(int(e))
            f2 = lambda e: pure(e * 10)
            f3 = kleisli(f1, f2)
            f4 = lambda e: left("err")
            f5 = kleisli(f3, f4)

            self.assertEquals(bind(pure("10"), f3), right(100))
            self.assertEquals(bind(pure("10"), f5), left("err"))

    class Laws(unittest.TestCase):
        def test_functor(self):
            f = lambda e: e + 10
            g = lambda e: e * 10
            g_of_f = lambda e: g(f(e))

            # fmap id x = x                  -- Identity
            self.assertEquals(fmap(identity, pure(5)), pure(5))

            # fmap (g . f) = fmap g . fmap f -- Composition
            self.assertEquals(fmap(g_of_f, pure(5)), fmap(g, fmap(f, pure(5))))

        def test_applicative(self):
            sup = lambda x: lambda f: f(x)
            comp2 = lambda g: lambda f: lambda x: g(f(x))
            u = lambda e: e + 10
            v = lambda e: e * 10

            # pure id <*> v = v                            -- Identity
            self.assertEquals(app(pure(identity), pure(1)), pure(1))

            # pure f <*> pure x = pure (f x)               -- Homomorphism
            self.assertEquals(app(pure(lambda e: e + 1), pure(1)), pure(2))

            # u <*> pure y = pure ($ y) <*> u              -- Interchange
            self.assertEquals(
                app(pure(lambda e: e + "!"), pure("hello")),
                app(pure(sup("hello")), pure(lambda e: e + "!")))

            # pure (.) <*> u <*> v <*> w = u <*> (v <*> w) -- Composition
            self.assertEquals(
                app(app(app(pure(comp2), pure(u)), pure(v)), pure(5)),
                app(pure(u), app(pure(v), pure(5))))

        def test_monad(self):
            # m >>= return     =  m                        -- Right Unit
            self.assertEquals(bind(pure(5), pure), pure(5))

            # return x >>= f   =  f x                      -- Left Unit
            self.assertEquals(bind(pure(5), lambda e: pure(e + 5)), pure(10))

            # (m >>= f) >>= g  =  m >>= (\x -> f x >>= g)  -- Associativity
            self.assertEquals(
                bind(bind(pure("5"), lambda e: pure(int(e))), lambda e: e + 5),
                bind(pure("5"), lambda e: bind(pure(int(e)), lambda e: e + 5)))

    unittest.main()
