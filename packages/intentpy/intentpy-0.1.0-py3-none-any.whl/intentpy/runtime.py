from .registry import FALLBACKS


class IntentSpec:
    """
    Declarative specification of an intent.
    """
    def __init__(self, name, requires, effects, on_fail):
        self.name = name
        self.requires = requires
        self.effects = effects
        self.on_fail = on_fail


class IntentFrame:
    """
    Represents one execution frame in the intent call stack.
    """
    def __init__(self, intent_spec, parent=None):
        self.intent = intent_spec
        self.parent = parent
        self.children = []


def log(ctx, message):
    indent = "  " * ctx.depth()
    print(f"{indent}{message}")


def handle_failure(ctx, frame: IntentFrame):
    intent = frame.intent

    log(ctx, f"[INTENT BLOCKED] {intent.name}")

    if intent.on_fail is None:
        raise RuntimeError(
            f"Intent '{intent.name}' failed with no fallback defined"
        )

    fallback_fn = FALLBACKS.get(intent.on_fail)
    if fallback_fn is None:
        raise ValueError(
            f"Fallback '{intent.on_fail}' is not registered"
        )

    return fallback_fn(ctx, intent)


def log_effects(ctx, intent_spec: IntentSpec):
    for effect in intent_spec.effects:
        log(ctx, f"[INTENT EFFECT] {intent_spec.name}: {effect}")
