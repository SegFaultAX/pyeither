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
        .bind(either.predicate(os.path.isfile, "not a file"))
        .bind(lambda p: either.attempt(json.load, p)))

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

I've created an IPython Notebook that describes the motivation for this project
as an interactive tutorial building an analogous system from scratch. If you're
interested in learning more about the **why** of this project, please check it
out!

[**Motivation Notebook**](https://github.com/SegFaultAX/pyeither/blob/master/pyeither_demo.ipynb)

## Special Thanks

This library depends on the absolutely wonderful
[`attrs`](http://www.attrs.org/en/stable/) library, without which there would
have been far more ugly boilerplate.

## License

Copyright 2018 Michael-Keith Bernard 

See LICENSE.txt for the full license.
