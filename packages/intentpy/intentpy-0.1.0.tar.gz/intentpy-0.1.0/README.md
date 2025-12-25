# intentpy

**intentpy** is a lightweight Python library for **intent-based execution** —
where *what you want to do* is declared separately from *whether it is allowed to happen*.

It provides:
- Declarative **preconditions**
- Explicit **fallback policies**
- **Nested intent execution**
- Structured, readable runtime traces

This is **not** a circuit breaker or workflow engine.
It is a semantic execution layer.

---

## Why intentpy?

Traditional decorators answer:
> “Should this function run?”

Intent-based execution answers:
> “What is the intent, what does it require, and what happens if it fails?”

This makes complex logic:
- composable
- debuggable
- intention-revealing

---

## Core Concepts

### Intent
An intent represents a meaningful action:
- it has **requirements**
- it produces **effects**
- it may **fail gracefully**

### Condition
Reusable boolean predicates that gate execution.

### Fallback
Named handlers that execute when an intent cannot proceed.

### Nesting
Intents can call other intents.
Execution is tracked as a runtime tree.

---

## Example: Nested Intent Execution

```python
from intentpy import intent, condition, fallback, ExecutionContext


class User:
    def __init__(self, authenticated: bool):
        self.is_authenticated = authenticated


@condition("user_authenticated")
def is_authenticated(ctx):
    return ctx.user.is_authenticated


@fallback("log_only")
def log_only(ctx, intent):
    print(f"Handled failure for intent: {intent.name}")


@intent(
    name="send_email",
    requires=["user_authenticated"],
    effects=["email_sent"],
    on_fail="log_only"
)
def send_email(ctx):
    print("Sending email...")


@intent(
    name="process_order",
    requires=["user_authenticated"],
    effects=["order_processed"],
    on_fail="log_only"
)
def process_order(ctx):
    send_email(ctx=ctx)


ctx = ExecutionContext(user=User(authenticated=True))
process_order(ctx=ctx)
