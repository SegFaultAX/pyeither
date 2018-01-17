# pyeither

A functional Python library that exposes `Data.Either` from Haskell.

```haskell
data Either e a = Left e | Right a
```

## Example Usage

```python
import os
import json
import either

def main():
    path = "~/myfile.json"
    
    # Lift a normal value into Either
    e_path = either.pure(path)

    # Ensure the path is valid, returning Right(path) if it is or Left("not a file") if it isn't
    e_valid = e_path.bind(either.predicate(os.path.isfile, "not a file"))

    # Load a file as json, returning Right(contents) if it works, or Left(exc) if it doesn't
    e_data = e_valid.bind(lambda p: either.attempt(json.load, p))

    # It's annoying to assign intermediate values to variables, so you can chain expressions
    # Equivalent to above:

    e_data2 = (either.pure(path)
        .chain()
        .bind(either.predicate(os.path.isfile, "not a file"))
        .bind(lambda p: either.attempt(json.load, p))
        .unchain())

    # Python lacks do-notation, so there's not a nice equivalent syntax

    # Build pipelines of actions using monadic composition

    ensure_path = either.predicate(os.path.isfile, "not a file")
    load_file = lambda p: either.attempt(json.load, p)

    process = either.kleisli(ensure_path, load_file)

    # Equivalent to above:
    e_data3 = either.pure(path).bind(process)
```

## Getting pyeither

```
pip install pyeither
```

## Motivation

pyeither introduces a form of effectful programming to Python. Specifically,
`Either` represents the effect of "failure", which is to say that it can be used
to model computations that can either complete successfully or fail with an
error. The specific implementation of `Either` found in this library is closely
modeled after the `Data.Either` implementation in Haskell. For those familiar
with Haskell, I've included relevant type information in the docstrings for all
top-level functions.

Note: What follows is not a Monad tutorial. Any resemblance to a Monad tutorial
is purely coincidental. ;)

### Intuition for Either

To start building an intuition for how one might use `Either`, it's instructive
to look at some examples of how one might solve problems similar to what
`Either` is meant to solve, and slowly build towards Either. The remainder of
this section will build an analogous solution to `Either`, starting from more
typical Python code and working towards the desired solution.

Consider the following function:

```python
def ten_divided_by(n):
    if n == 0:
        raise ArgumentError("argument cannot be zero")
    return 10 / n
```

While this example is a little contrived, it's fairly typical in the way it
operates. 

TODO: ... exposition on why exceptions and alternatives are subpar ...

One alternative approach to using exceptions or return codes/flags is to create
a very simple data type that we can use to wrap a result (if there is one) or a
failure if something went wrong. There are a few ways to model such a data type,
but we'll start with the Simplest Possible Thing That Will Work: a class with 2
members, one to store whether or not we represent a "successful" value, and the
value itself.

```python
import attr

@attr.s(frozen=True, repr=False)
class Perhaps:
    """A container for a possibly successful result"""

    success = attr.ib()
    value = attr.ib()

    @property
    def failure(self):
        return not self.success

    def __repr__(self):
        if self.success:
            return "Success({})".format(self.value)
        else:
            return "Failure"

fail = Perhaps(False, None)

def succeed(v):
    return Perhaps(True, v)
```

Note: If you're not familiar with the [attrs](http://www.attrs.org/en/stable/)
library, you should fix that immediately! It's a wonderful little library and
really helps reduce boilerplate in object oriented Python code.

What have we actually created here? You can think of `Perhaps` as being a value
in one of two states: either it's nothing at all, or it's the successful result
of the computation. The function `succeed` gives us a way to lift a normal value
into the `Perhaps` context. Let's see how we can use this rather barebones type:

```python
print(fail)       #=> Failure
print(succeed(3)) #=> Success(3)

def div(a, b):
    if b == 0:
        return fail
    else:
        return succeed(a / b)

print(div(10, 5)) #=> Success(2)
print(div(10, 0)) #=> Failure
```

Great! We've created a very basic way to indicate that a function has succeeded
or failed. If some function `f` returns `fail`, then we know something went
wrong, or else if it returns `Success(v)`, then the value `v` inside the
`Perhaps` is a successful result.

Unfortunately this class isn't yet very useful. For starters, because we have a
`Perhaps` value wrapping our possible-result, we can't easily apply a normal
function (ie, a function that doesn't use `Perhaps`) to the result. To solve
that problem, we'll define a method on perhaps called `inside` which, given a
normal function, will apply it to the result if it's a success, or do nothing at
all if it's a failure.

```python
class Perhaps:
   # ... SNIP ...
   def inside(self, f):
       """Apply function `f` to my value if I'm a success, or else fail"""

       if self.success:
           return succeed(f(self.value))
       else:
           return fail

a = div(6, 2)
b = a * 10 # This is an error because `a` is Perhaps(3), not 3

b = a.inside(lambda v: v * 10)
print(b) #=> Success(30)

c = fail.inside(lambda v: v * 10)
print(c) #=> Failure
```

`inside` gives us a way to lift normal functions into the context of `Perhaps`.
Stated another way, they allow us to convert a function that knows nothing about
the `Perhaps` type into a function that can properly handle values nested inside
of a possibly-failed context!

The method `inside` works great for those cases where the function we want to
apply is normal (again, normal in this context means that it doesn't use
`Perhaps` to indicate success or failure). But what if we want to apply a
function that also uses `Perhaps` to indicate its failure?

```python
def always_succeed(n):
    return succeed(n)

def always_fail(n):
    return fail

# Example: Success case
a = succeed(10)          # Success(10)
a.inside(always_succeed) # Success(Success(10))
a.inside(always_fail)    # Success(Failure)

# Example: Failure case
fail.inside(always_succeed) # Failure
fail.inside(always_fail)    # Failure
```

Remember that `inside` is just applying the function to our possible-result. In
the failure case above, our function is never applied because there is no value
to apply it to, so the result is what we expect. However some interesting
happens in success case: the result of `always_succeed` inside `succeed(10)` is
`Success(Success(10))`, the inner `Success` being the result of the call to
`always_succeed(10)`. Likewise, the result of `always_fail` is
`Success(Failure)`, or in other words a failed result inside of a successful
result.

To solve this problem, we can implement a simple function called `collapse`
which, given a successful value, will reduce one level of nested `Perhaps`. In
other words, the result of `Success(Success(10)).collapse()` will be
`Success(10)`, the result of `Success(Failure).collapse()` will be `Failure`,
and so on.


```python
class Perhaps:
    # ... SNIP ...
    def collapse(self):
        if self.success:
            return self.value
        else:
            return fail

succeed(succeed(10)).collapse() # Success(10)
succeed(fail).collapse()        # Failure
fail.collapse()                 # Failure
```

Imagine a scenario where you're going to build up a pipeline of functions, each
of which can independently fail for its own reasons, and you wish to chain these
functions together such that the result of one funtion serves as the input to
the next. Consider the following (somewhat contrived) example:


```python
import os
import yaml

def ensure_path(path):
    return succeed(path) if os.path.exists(path) else fail

def read_file(path):
    try:
        return open(path).read()
    except:
        return fail

def parse_content(content):
    try:
        return yaml.safe_load(content)
    except:
        return fail

def process(path):
    return succeed(path) \
        .inside(ensure_path).collapse() \
        .inside(read_file).collapse() \
        .inside(parse_content).collapse()

process("~/config.yaml") # {"foo": 123, "bar": 456, ...}
```

Notice the repetition of `.inside(__).collapse()`. Why is that necessary? Recall
that `inside` is just applying the function to our possible-result so far which,
if the function happens to use `Perhaps` to indicate success, means our value
quickly becomes deeply nested. The `collapse` method was specifically added to
reduce one layer of nesting after applying such a function. It turns out that
the pattern of `.inside(f).collapse()` is so common, that we can reduce some
boilerpalte by wrapping it in a method that accepts a `Perhaps`-returning
function, applies it, then collapses the resulting layer of nesting.

```python
class Perhaps:
    # ... SNIP ...
    def and_then(self, f):
        return self.inside(f).collapse()

def process(path):
    return succeed(path) \
        .and_then(ensure_path) \
        .and_then(read_file) \
        .and_then(parse_content)
```

And now we've arrived at a very useful abstraction for using and chaining
possibly failing computations. The entire implementation of `Perhaps` is as
follows:

```python
import attr

def identity(v):
    """Identity function"""

    return v

@attr.s(frozen=True, repr=False)
class Perhaps:
    """A container for a possibly successful result"""

    success = attr.ib()
    value = attr.ib()

    @property
    def failure(self):
        return not self.success

   def inside(self, f):
       """Apply function `f` to my value if I'm a success, or else fail"""

       if self.success:
           return succeed(f(self.value))
       else:
           return fail

    def collapse(self):
        """Remove one layer of nesting"""

        return self.and_then(identity)

    def and_then(self, f):
        if self.success:
            return f(self.value)
        else:
            return fail

    def __repr__(self):
        if self.success:
            return "Success({})".format(self.value)
        else:
            return "Failure"

fail = Perhaps(False, None)

def succeed(v):
    return Perhaps(True, v)
```

### Monads and the rest

The construction we created in the last section is actually a well known type
typically refered to as `Maybe` or `Optional` in other languages. Furthermore,
each of the methods we added (`inside`, `collapse`, `and_then`) have well known
names and semantics from the functional world. They are:

* `inside` - `fmap` or `map`, typically associated with the typeclass Functor
* `collapse` - `join` or `flatten`, typically associated with the typeclass
  Monad
* `and_then` - `flatMap` or `bind`, typically assocated with the typeclass Monad

If you're interested in learning more about Monads and the like, I strongly
recommend [this article](http://blog.sigfpe.com/2006/08/you-could-have-invented-monads-and.html)
as a starting point.

### Back to pyeither

I hope that now you have a better intuition about how we can build a simple
library that allows us to generically model failure in a convenient way.
pyeither aims to provide an interface that is similar to the `Perhaps` type
described above, with a few key differences:

* `Either`'s "failure" state can carry a value in the same way that it's
  "success" state can. Whereas in the `Perhaps` case you have just `fail` or
  `succeed(x)`, in `Either` you have `fail(err)` and `succeed(result)`. This
  additional failure value allows you to pass context as to **why** something
  failed down the chain.

* `Either` is totally generic, and can be used to model an arbitrary union of
  types (although `either.bind` is right-associative).

* There are many more combinators than just the ones shown for `Perhaps` above,
  all of which are well-tested and well-behaved according to their associated
  laws (Functor, Applicative, Monad, etc)

## Special Thanks

This library depends on the absolutely wonderful
[`attrs`](http://www.attrs.org/en/stable/) library, without which there would
have been far more ugly boilerplate.

## License

Copyright 2018 Michael-Keith Bernard 

See LICENSE.txt for the full license.
