from intentpy import intent, condition, fallback, ExecutionContext


@condition("always_true")
def always_true(ctx):
    return True


@condition("always_false")
def always_false(ctx):
    return False


@fallback("noop")
def noop(ctx, intent):
    return "failed"


@intent(
    name="success_intent",
    requires=["always_true"],
    effects=["done"]
)
def success(ctx):
    return "ok"


@intent(
    name="fail_intent",
    requires=["always_false"],
    on_fail="noop"
)
def fail(ctx):
    return "should_not_run"


def test_success():
    ctx = ExecutionContext()
    assert success(ctx=ctx) == "ok"


def test_failure():
    ctx = ExecutionContext()
    assert fail(ctx=ctx) == "failed"
