from .state import load_state

# -------------------------------------------------
# EXISTING FUNCTIONS (UNCHANGED)
# -------------------------------------------------

def show_badges():
    """
    Evaluate achievements and return a printable badge list.

    This is the PUBLIC entrypoint that:
    - loads achievement rules
    - evaluates them
    - persists newly earned badges
    """
    from devopsmind.achievements import show_badges as _evaluate_and_render

    # NOTE:
    # We intentionally call the achievements-layer function
    # to trigger evaluation side effects.
    return _evaluate_and_render()


# -------------------------------------------------
# Delta badge helper (NO HARD-CODED RULES)
# -------------------------------------------------

def evaluate_badges_delta(trigger_fn, *args, **kwargs):
    """
    Generic wrapper to compute newly earned badges (delta).

    - DOES NOT contain badge rules
    - DOES NOT decide eligibility
    - Delegates evaluation to achievements layer
    """

    # Snapshot BEFORE
    state_before = load_state()
    before = set(state_before.get("badges", []))

    # Run progress mutation (e.g. record_completion)
    trigger_fn(*args, **kwargs)

    # 🔒 Trigger achievement evaluation (PUBLIC API)
    show_badges()

    # Snapshot AFTER
    state_after = load_state()
    after = set(state_after.get("badges", []))

    return sorted(after - before)
