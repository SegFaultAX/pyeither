#!/usr/bin/env python

import unittest

import attr

from either import *

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
        self.assertEqual(Left("foo").get(), "foo")
        self.assertEqual(left("foo").get(), "foo")

    def test_right(self):
        self.assertEqual(Right("foo").get(), "foo")
        self.assertEqual(right("foo").get(), "foo")

    def test_fmap(self):
        self.assertEqual(fmap(lambda e: e + 1, right(1)), right(2))
        self.assertEqual(fmap(lambda e: e + 1, left("err")), left("err"))

    def test_app(self):
        self.assertEqual(app(right(lambda e: e + 1), right(1)), right(2))
        self.assertEqual(app(right(lambda e: e + 1), left("err")), left("err"))
        self.assertEqual(app(left("err1"), left("err2")), left("err1"))

    def test_lift(self):
        add = lambda a, b: a + b
        self.assertEqual(lift(add)(pure(1), pure(2)), pure(3))
        self.assertEqual(lift(add)(pure(1), left("err")), left("err"))
        self.assertEqual(lift(add)(left("err1"), pure("err2")), left("err1"))

    def test_pure(self):
        self.assertEqual(pure(1), right(1))

    def test_bind(self):
        self.assertEqual(bind(pure(1), lambda e: right(e + 1)), right(2))
        self.assertEqual(bind(left("err"), lambda e: right(e + 1)), left("err"))

    def test_combine(self):
        self.assertEqual(combine(pure(1), pure(2)), pure(1))
        self.assertEqual(combine(left("err"), pure(2)), pure(2))
        self.assertEqual(combine(left("err"), left("err!")), left("err!"))

    def test_bimap(self):
        lf = lambda e: e + "!"
        rf = lambda e: e + 1
        self.assertEqual(bimap(lf, rf, right(1)), right(2))
        self.assertEqual(bimap(lf, rf, left("err")), left("err!"))

    def test_first_second(self):
        l = left("err")
        r = right(1)
        self.assertEqual(first(lambda e: e + "!", l), left("err!"))
        self.assertEqual(first(lambda e: e + "!", r), right(1))
        self.assertEqual(second(lambda e: e + 1, l), left("err"))
        self.assertEqual(second(lambda e: e + 1, r), right(2))

    def test_foldr(self):
        self.assertEqual(foldr(lambda e, v: e / v, 2, pure(10)), 5)
        self.assertEqual(foldr(lambda e, v: e / v, 2, left("err")), 2)

    def test_traverse(self):
        self.assertEqual(traverse(lambda e: Id(e * 2), pure(5), Id), Id(pure(10)))
        self.assertEqual(traverse(lambda e: Id(e * 2), left("err"), Id), Id(left("err")))

    def test_sequence(self):
        self.assertEqual(sequence(pure(Id(1)), Id), Id(pure(1)))
        self.assertEqual(sequence(left("err"), Id), Id(left("err")))

    def test_traverseL(self):
        bad_even = lambda n: left("err" + str(n)) if n % 2 == 0 else pure(n)

        self.assertEqual(traverseL(pure, [1,2,3,4]), pure([1,2,3,4]))
        self.assertEqual(traverseL(bad_even, [1,2,3,4]), left("err2"))

    def test_sequenceL(self):
        self.assertEqual(sequenceL([pure(1), pure(2), pure(3)]), pure([1,2,3]))
        self.assertEqual(sequenceL([pure(1), left("err1"), left("err2"), pure(3)]), left("err1"))

    def test_join(self):
        self.assertEqual(join(pure(pure(5))), pure(5))

    def test_lmap(self):
        self.assertEqual(lmap(lambda e: e + "!", right(1)), right(1))
        self.assertEqual(lmap(lambda e: e + "!", left("err")), left("err!"))

    def test_attempt(self):
        def angry():
            raise RuntimeError("so angry")
        self.assertTrue(attempt(angry).is_left)
        self.assertTrue(isinstance(attempt(angry).get(), RuntimeError))
        self.assertEqual(attempt(lambda e: e, 5), pure(5))

    def test_should(self):
        self.assertEqual(should(True, 1, "err"), pure(1))
        self.assertEqual(should(False, 1, "err"), left("err"))

    def test_predicate(self):
        self.assertEqual(predicate(lambda e: True, "err")(1), pure(1))
        self.assertEqual(predicate(lambda e: False, "err")(1), left("err"))

    def test_chain(self):
        c1 = pure(1).fmap(lambda e: e + 1).bind(lambda e: pure(e * 2))
        self.assertEqual(c1, right(4))

        c2 = pure(1).bind(lambda _: left("err")).lmap(lambda e: e + "!")
        self.assertEqual(c2, left("err!"))

        lf = lambda e: e + "!"
        rf = lambda e: e * 10
        c3 = pure(lambda e: e + 1).app(pure(1)).bimap(lf, rf)
        self.assertEqual(c3, right(20))

    def test_kleisli(self):
        f1 = lambda e: pure(int(e))
        f2 = lambda e: pure(e * 10)
        f3 = kleisli(f1, f2)
        f4 = lambda e: left("err")
        f5 = kleisli(f3, f4)

        self.assertEqual(bind(pure("10"), f3), right(100))
        self.assertEqual(bind(pure("10"), f5), left("err"))

    def test_partition_eithers(self):
        l = [left("err1"), right(1), left("err2"), right(2)]
        self.assertEqual(partition_eithers(l), (["err1", "err2"], [1, 2]))

    def test_lefts_rights(self):
        l = [left("err1"), right(1), left("err2"), right(2)]
        self.assertEqual(lefts(l), ["err1", "err2"])
        self.assertEqual(rights(l), [1, 2])

    def test_is_left_right(self):
        self.assertTrue(is_left(left("err")))
        self.assertFalse(is_left(right(1)))

        self.assertTrue(is_right(right(1)))
        self.assertFalse(is_right(left("err")))

    def test_either(self):
        f = lambda _e: 0
        g = lambda _e: 1

        self.assertEqual(either(f, g, left("err")), 0)
        self.assertEqual(either(f, g, right(1234)), 1)

class Laws(unittest.TestCase):
    def test_functor(self):
        f = lambda e: e + 10
        g = lambda e: e * 10
        g_of_f = lambda e: g(f(e))

        # fmap id x = x                  -- Identity
        self.assertEqual(fmap(identity, pure(5)), pure(5))

        # fmap (g . f) = fmap g . fmap f -- Composition
        self.assertEqual(fmap(g_of_f, pure(5)), fmap(g, fmap(f, pure(5))))

    def test_applicative(self):
        sup = lambda x: lambda f: f(x)
        comp2 = lambda g: lambda f: lambda x: g(f(x))
        u = lambda e: e + 10
        v = lambda e: e * 10

        # pure id <*> v = v                            -- Identity
        self.assertEqual(app(pure(identity), pure(1)), pure(1))

        # pure f <*> pure x = pure (f x)               -- Homomorphism
        self.assertEqual(app(pure(lambda e: e + 1), pure(1)), pure(2))

        # u <*> pure y = pure ($ y) <*> u              -- Interchange
        self.assertEqual(
            app(pure(lambda e: e + "!"), pure("hello")),
            app(pure(sup("hello")), pure(lambda e: e + "!")))

        # pure (.) <*> u <*> v <*> w = u <*> (v <*> w) -- Composition
        self.assertEqual(
            app(app(app(pure(comp2), pure(u)), pure(v)), pure(5)),
            app(pure(u), app(pure(v), pure(5))))

    def test_monad(self):
        # m >>= return     =  m                        -- Right Unit
        self.assertEqual(bind(pure(5), pure), pure(5))

        # return x >>= f   =  f x                      -- Left Unit
        self.assertEqual(bind(pure(5), lambda e: pure(e + 5)), pure(10))

        # (m >>= f) >>= g  =  m >>= (\x -> f x >>= g)  -- Associativity
        self.assertEqual(
            bind(bind(pure("5"), lambda e: pure(int(e))), lambda e: e + 5),
            bind(pure("5"), lambda e: bind(pure(int(e)), lambda e: e + 5)))
