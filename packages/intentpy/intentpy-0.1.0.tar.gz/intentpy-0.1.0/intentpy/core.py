from .registry import CONDITIONS
from .runtime import IntentSpec, IntentFrame, handle_failure, log_effects, log


def intent(name, requires=None, effects=None, on_fail=None):
    """
    Decorator to declare intent-aware execution with nesting support.
    """
    requires = requires or []
    effects = effects or []

    def decorator(fn):
        intent_spec = IntentSpec(
            name=name,
            requires=requires,
            effects=effects,
            on_fail=on_fail
        )

        def wrapper(*args, **kwargs):
            ctx = kwargs.get("ctx")
            if ctx is None:
                raise ValueError(
                    "ExecutionContext must be provided as keyword argument 'ctx'"
                )

            parent = ctx.current_intent()
            frame = IntentFrame(intent_spec, parent)

            if parent:
                parent.children.append(frame)

            ctx.push_intent(frame)
            log(ctx, f"[INTENT] {intent_spec.name}")

            try:
                # 1. Check preconditions
                for cond_name in intent_spec.requires:
                    cond_fn = CONDITIONS.get(cond_name)
                    if cond_fn is None:
                        raise ValueError(
                            f"Condition '{cond_name}' is not registered"
                        )

                    if not cond_fn(ctx):
                        return handle_failure(ctx, frame)

                # 2. Execute function
                result = fn(*args, **kwargs)

                # 3. Log effects
                log_effects(ctx, intent_spec)

                return result

            finally:
                ctx.pop_intent()

        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper

    return decorator
