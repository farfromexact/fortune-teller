"""Idempotent casting events, independent of browser animation and the LLM."""

def accept_toss(state, event) -> bool:
    if not isinstance(event, dict) or state.get("stage") != "cast":
        return False
    index = event.get("index")
    if event.get("run_id") != state.get("cast_run_id") or type(index) is not int or index != len(state["lines"]) + 1 or index > 6:
        return False
    # Streamlit can evict imported modules during a source update while a
    # registered callback still retains this function's old globals. Resolve
    # the engine on each accepted event instead of retaining a stale module.
    from guanbian_engine import cast_coins

    coins = list(cast_coins())
    history = state.get("coin_tosses")
    # A hot-reloaded older session may have sums but no coin-face history.
    state["coin_tosses"] = [*history, coins] if isinstance(history, list) and len(history) == len(state["lines"]) else None
    state["last_coins"] = coins
    state["lines"] = [*state["lines"], sum(coins)]
    return True
