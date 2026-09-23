"""Idempotent casting events, independent of browser animation and the LLM."""

import guanbian_engine as engine


def accept_toss(state, event) -> bool:
    if not isinstance(event, dict) or state.get("stage") != "cast":
        return False
    index = event.get("index")
    if event.get("run_id") != state.get("cast_run_id") or type(index) is not int or index != len(state["lines"]) + 1 or index > 6:
        return False
    coins = list(engine.cast_coins())
    history = state.get("coin_tosses")
    # A hot-reloaded older session may have sums but no coin-face history.
    state["coin_tosses"] = [*history, coins] if isinstance(history, list) and len(history) == len(state["lines"]) else None
    state["last_coins"] = coins
    state["lines"] = [*state["lines"], sum(coins)]
    return True
