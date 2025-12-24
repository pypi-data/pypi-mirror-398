# `simulate-argument-binding`

A pure Python library to simulate Python's internal argument binding given function signature details, default values,
and user-provided arguments/keywords. Useful for code analysis, code generation, and implementing custom dispatch or
validation logic.

## Installation

```bash
pip install simulate-argument-binding
```

## Examples

```python
from __future__ import print_function
from simulate_argument_binding import simulate_argument_binding

# 1. All Required Arguments Provided
binding = simulate_argument_binding(
    posonlyargs=['x'],
    args=['y'],
    vararg=None,
    kwonlyargs=['z'],
    varkwarg=None,
    defaults={},
    provided_args=[3, 4],
    provided_kwargs={'z': 5}
)
assert list(binding.items()) == [('x', 3), ('y', 4), ('z', 5)]

# 2. Default Values and Overriding
binding = simulate_argument_binding(
    posonlyargs=['a'],
    args=['b', 'c'],
    vararg=None,
    kwonlyargs=['d'],
    varkwarg=None,
    defaults={'b': 2, 'c': 3, 'd': 4},
    provided_args=[9, 8],  # a=9, b=8 overrides default
    provided_kwargs={}
)
assert list(binding.items()) == [('a', 9), ('b', 8), ('c', 3), ('d', 4)]

# 3. Var-positional (`*args`) and Var-keyword (`**kwargs`)
binding = simulate_argument_binding(
    posonlyargs=[],
    args=['x'],
    vararg='args',
    kwonlyargs=[],
    varkwarg='kwargs',
    defaults={},
    provided_args=[1, 2, 3, 4],
    provided_kwargs={'foo': 10, 'bar': 20}
)
assert list(binding.items()) == [
    ('x', 1),
    ('args', (2, 3, 4)),
    ('kwargs', {'foo': 10, 'bar': 20})
]

# 4. Keyword-only Arguments
binding = simulate_argument_binding(
    posonlyargs=[],
    args=[],
    vararg=None,
    kwonlyargs=['k1', 'k2'],
    varkwarg=None,
    defaults={'k2': 5},
    provided_args=[],
    provided_kwargs={'k1': 1}
)
assert list(binding.items()) == [
    ('k1', 1),
    ('k2', 5)
]

# 5. Detect Missing Required Arguments
try:
    simulate_argument_binding(
        posonlyargs=['a'],
        args=['b'],
        vararg=None,
        kwonlyargs=[],
        varkwarg=None,
        defaults={},
        provided_args=[],
        provided_kwargs={}
    )
except TypeError as ex:
    assert "Missing positional-only arguments" in str(ex) or "Missing arguments" in str(ex)
else:
    assert False, "Should have raised TypeError"

# 6. Detect Duplicate Assignment
try:
    simulate_argument_binding(
        posonlyargs=[],
        args=['x'],
        vararg=None,
        kwonlyargs=[],
        varkwarg=None,
        defaults={},
        provided_args=[1],
        provided_kwargs={'x': 2}
    )
except TypeError as ex:
    assert "multiple values for argument 'x'" in str(ex)
else:
    assert False, "Should have raised TypeError"

# 7. Detect Extra Positional/Keyword Args when Not Allowed
try:
    simulate_argument_binding(
        posonlyargs=[],
        args=['a'],
        vararg=None,
        kwonlyargs=[],
        varkwarg=None,
        defaults={},
        provided_args=[1, 2],
        provided_kwargs={}
    )
except TypeError as ex:
    assert "extra positional arguments" in str(ex)
else:
    assert False, "Should have raised TypeError"

try:
    simulate_argument_binding(
        posonlyargs=['a'],
        args=[],
        vararg=None,
        kwonlyargs=[],
        varkwarg=None,
        defaults={},
        provided_args=[5],
        provided_kwargs={'oops': 1}
    )
except TypeError as ex:
    assert "extra keyword arguments" in str(ex)
else:
    assert False, "Should have raised TypeError"

# 8. Advanced: Mixing All Kinds
binding = simulate_argument_binding(
    posonlyargs=['a'],
    args=['b'],
    vararg='c',
    kwonlyargs=['d'],
    varkwarg='e',
    defaults={'b': 2, 'd': 3},
    provided_args=[1, 99, 7, 8, 9],  # a=1, b=99, *c=(7,8,9)
    provided_kwargs={'d': 42, 'extra1': 'x', 'extra2': 'y'}
)
assert list(binding.items()) == [
    ('a', 1),
    ('b', 99),
    ('c', (7, 8, 9)),
    ('d', 42),
    ('e', {'extra1': 'x', 'extra2': 'y'})
]
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## License

This project is licensed under the [MIT License](LICENSE).