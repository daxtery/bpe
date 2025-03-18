from collections import Counter

from bpe import Pair, State, from_text, step


def test_noop():
    state = from_text("abc")
    next_state = step(state)
    assert next_state == state


def test_easy():
    state = from_text("aaa")
    a_id = ord("a")
    next_state = step(state)
    assert next_state == State(
        [256, a_id],
        Counter(
            {
                Pair(256, a_id): 1,
                Pair(a_id, a_id): 0,
            }
        ),
        {**state.token_map, 256: Pair(a_id, a_id)},
    )
