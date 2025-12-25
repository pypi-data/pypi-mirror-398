# Pystitia

A lightweight Python library for Design by Contract (DbC) programming, enabling you to specify preconditions and postconditions for your functions.

## Overview

Pystitia brings the power of Design by Contract to Python through simple decorators. Define what must be true before your function runs (preconditions) and what must be true after it completes (postconditions), making your code more reliable and self-documenting.

### Pystitia - the name

Pystitia takes its name from Justitia, the Roman goddess of justice, who is traditionally depicted holding scales to weigh evidence and a sword to execute judgment. Just as Justitia enforces fairness through balanced evaluation of obligations and rights, pystitia enforces software correctness by balancing the obligations between callers (preconditions) and implementers (postconditions). The name reflects the library's core principle: that code should honor its contracts with the same rigor that justice demands adherence to law.

## Installation

```bash
pip install pystitia
```

## Quick Start

```python
from pystitia import contracts, setTestMode

# Enable contract checking
setTestMode(True)

@contracts(
    preconditions=[
        lambda x: x > 0,
        lambda x: isinstance(x, (int, float))
    ],
    postconditions=[
        lambda __return__: __return__ > 0
    ]
)
def square_root(x):
    return x ** 0.5

# This works
result = square_root(16)  # Returns 4.0

# This raises PreConditionError
result = square_root(-5)  # Negative number violates precondition
```

## Features

### Preconditions

Preconditions specify what must be true before a function executes. They represent the caller's obligations.

```python
@contracts(
    preconditions=[
        lambda balance, amount: amount > 0,
        lambda balance, amount: balance >= amount
    ]
)
def withdraw(balance, amount):
    return balance - amount
```

### Postconditions

Postconditions specify what the function guarantees after execution. They can access:
- `__return__`: The function's return value
- `__old__`: A namespace containing deep copies of all arguments before execution
- `__id__`: A namespace containing the original object IDs for mutability checks
- All original function arguments

```python
@contracts(
    postconditions=[
        lambda __return__, amount: __return__ == __old__.balance - amount,
        lambda __old__, balance: id(balance) == __id__.balance  # Ensure immutability
    ]
)
def withdraw(balance, amount):
    return balance - amount
```

### Checking Object Mutations

Pystitia allows you to verify whether objects were modified during function execution:

```python
@contracts(
    postconditions=[
        lambda data, __id__: id(data) == __id__.data  # Verify list wasn't replaced
    ]
)
def append_item(data, item):
    data.append(item)
    return data
```

### Test Mode Control

Enable or disable contract checking at runtime. This is useful for disabling overhead in production:

```python
from pystitia import setTestMode

# Enable contract checking (recommended for development/testing)
setTestMode(True)

# Disable contract checking (for production)
setTestMode(False)
```

**Important:** You must call `setTestMode()` before using any decorated functions, or a `NameError` will be raised.

## Complete Example

```python
from pystitia import contracts, setTestMode

setTestMode(True)

class BankAccount:
    def __init__(self, initial_balance):
        self.balance = initial_balance
    
    @contracts(
        preconditions=[
            lambda self, amount: amount > 0,
            lambda self, amount: self.balance >= amount
        ],
        postconditions=[
            lambda self, __old__: self.balance == __old__.balance - amount,
            lambda self: self.balance >= 0
        ]
    )
    def withdraw(self, amount):
        self.balance -= amount
        return self.balance
    
    @contracts(
        preconditions=[
            lambda self, amount: amount > 0
        ],
        postconditions=[
            lambda self, __old__, amount: self.balance == __old__.balance + amount
        ]
    )
    def deposit(self, amount):
        self.balance += amount
        return self.balance

# Usage
account = BankAccount(100)
account.deposit(50)   # balance = 150
account.withdraw(30)  # balance = 120
account.withdraw(200) # Raises PreConditionError: insufficient funds
```

## Writing Condition Functions

Condition functions should:
- Return `True` if the condition is satisfied
- Return `False` if the condition is violated
- Accept only the parameters they need from the decorated function
- Use lambda functions for simple conditions
- Use named functions for complex conditions

```python
def is_positive(x):
    """Check if value is positive."""
    return x > 0

def valid_email(email):
    """Check if email format is valid."""
    return '@' in email and '.' in email.split('@')[1]

@contracts(
    preconditions=[is_positive, valid_email]
)
def send_notification(user_id, email):
    # Function implementation
    pass
```

## Special Variables in Postconditions

- `__return__`: The value returned by the function
- `__old__.param_name`: Deep copy of the parameter before function execution
- `__id__.param_name`: Original object ID of the parameter (for mutability checks)

## Error Handling

Pystitia raises two custom exceptions:

- `PreConditionError`: Raised when a precondition fails
- `PostConditionError`: Raised when a postcondition fails

Both exceptions include:
- Function name
- File path
- Line number
- Indices of failed condition functions

```python
from pystitia import PreConditionError, PostConditionError

try:
    result = some_function(invalid_input)
except PreConditionError as e:
    print(f"Invalid input: {e}")
except PostConditionError as e:
    print(f"Function violated its contract: {e}")
```

## Performance Considerations

- Contract checking adds runtime overhead due to:
  - Condition function calls
  - Deep copying of arguments for postconditions (when `__old__` is used)
  - Additional introspection

- Use `setTestMode(False)` in production to disable all contract checking
- Consider the cost of deep copying large data structures
- Write efficient condition functions

## Best Practices

1. **Keep conditions simple**: Each condition should check one thing
2. **Use descriptive names**: For complex conditions, use named functions with docstrings
3. **Test both paths**: Verify that conditions properly catch violations
4. **Enable in development**: Always run with `setTestMode(True)` during development
5. **Document side effects**: Use postconditions to document and verify intentional mutations
6. **Fail fast**: Design preconditions to catch errors as early as possible

## Limitations

- Requires explicit `setTestMode()` call before use
- Deep copying adds overhead for postconditions using `__old__`
- Decorated functions lose their original signature (affects IDE autocomplete)
- No support for class invariants (yet)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

**Note**: This library is intended primarily for development and testing. For production use, consider disabling contract checking with `setTestMode(False)` to avoid performance overhead.
