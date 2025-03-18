import itertools
import sys
from collections import Counter
from dataclasses import dataclass
from typing import cast

type TokenId = int
type TokenMap = dict[TokenId, Pair | TokenId]
type Frequencies = Counter[Pair]


@dataclass(frozen=True, slots=True)
class Pair:
    left: TokenId
    right: TokenId


def create_or_get_pair(map: TokenMap, pair: Pair) -> TokenId:
    for the_token, the_pair in map.items():
        if the_pair == pair:
            return the_token
    next_id = len(map)
    map[next_id] = pair
    return next_id


@dataclass(frozen=True, slots=True)
class State:
    # abcd@256
    tokens: list[TokenId]
    # a, @256 = 2
    frequencies: Counter[Pair]
    # @256 = a, b
    token_map: TokenMap

    def _expand_token(self, token: TokenId) -> list[str]:
        characters: list[str] = []
        to_process: list[TokenId] = [token]

        while to_process:
            token_id = to_process.pop()
            mapping = self.token_map[token_id]
            if isinstance(mapping, Pair):
                to_process.append(mapping.right)
                to_process.append(mapping.left)
            else:
                characters.append(chr(mapping))

        return characters

    def to_text(self) -> str:
        characters = []
        for token in self.tokens:
            characters.extend(self._expand_token(token))
        return "".join(characters)


def from_text(text: str) -> "State":
    token_map = cast(TokenMap, {i: i for i in range(256)})
    frequencies = Counter[Pair](
        (
            Pair(left=ord(left), right=ord(right))
            for left, right in itertools.pairwise(text)
        )
    )
    tokens = [ord(i) for i in text]
    return State(
        tokens,
        frequencies,
        token_map,
    )


def account_for_substitution(
    frequencies: Frequencies,
    left_token: TokenId | None,
    the_pair: Pair,
    right_token: TokenId | None,
    new_token: TokenId,
) -> None:
    # abcd
    # bc replaced by @366
    if left_token:
        left_previous_pair = Pair(left_token, the_pair.left)
        frequencies[left_previous_pair] -= 1
        left_new_pair = Pair(left_token, new_token)
        frequencies[left_new_pair] += 1
    if right_token:
        right_previous_pair = Pair(the_pair.right, right_token)
        frequencies[right_previous_pair] -= 1
        right_new_pair = Pair(new_token, right_token)
        frequencies[right_new_pair] += 1
    frequencies[the_pair] -= 1


def step(state: State) -> State:
    pair_to_replace, count = most_used(state.frequencies)
    if count == 1:
        return state

    new_tokens: list[TokenId] = []
    new_frequencies = Counter(state.frequencies)
    new_token_map = dict(state.token_map)

    old_idx = 0
    while old_idx < len(state.tokens):
        if old_idx + 1 >= len(state.tokens):
            new_tokens.append(state.tokens[old_idx])
            break

        pair = Pair(state.tokens[old_idx], state.tokens[old_idx + 1])
        if pair != pair_to_replace:
            new_tokens.append(state.tokens[old_idx])
            old_idx += 1
            continue

        new_token = create_or_get_pair(new_token_map, pair)

        left_token = new_tokens[-1] if new_tokens else None
        right_token = (
            state.tokens[old_idx + 2] if old_idx + 2 < len(state.tokens) else None
        )
        account_for_substitution(
            new_frequencies, left_token, pair, right_token, new_token
        )

        new_tokens.append(new_token)
        old_idx += 2

    return State(
        tokens=new_tokens, frequencies=new_frequencies, token_map=new_token_map
    )


def debug_state(state: State):
    print_tokens(state)
    print_mapping(state)
    print_frequencies(state)


def print_frequencies(state: State):
    print("Frequencies:")

    for pair, count in state.frequencies.items():
        mapping_left = state.token_map[pair.left]
        mapping_right = state.token_map[pair.right]
        print("\t", end="")
        if isinstance(mapping_left, Pair):
            print(f"({pair.left:3})", end="")
        else:
            print(
                f"{repr(chr(pair.left)):>5}",
                end="",
            )
        print(",", end="")
        if isinstance(mapping_right, Pair):
            print(f"({pair.right:03})", end="")
        else:
            print(
                f"{repr(chr(pair.right)):>5}",
                end="",
            )
        print(f" -> {count}")


def print_mapping(state: State):
    print("Mapping:")

    for token, to in state.token_map.items():
        if not isinstance(to, Pair):
            continue
        expanded = state._expand_token(token)
        print(f"\t({token:03}) -> ({to.left:03}, {to.right:03}) aka {expanded}")


def print_tokens(state: State):
    print('Tokens:\n"""')

    for token in state.tokens:
        mapping = state.token_map[token]
        if isinstance(mapping, Pair):
            print(f"({token})", end="")
        else:
            print(chr(token), end="")

    print('\n"""')


def most_used(frequencies: Counter[Pair]):
    return frequencies.most_common(1)[0]


def main(debug: bool = False):
    text = (
        sys.argv[1]
        if len(sys.argv) > 1
        else """
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
The quick brown fox jumps over the lazy dog
"""
    )
    state = from_text(text)
    i = 0

    while most_used(state.frequencies)[1] > 1:
        if debug:
            print(f"-- State -- iteration: {i + 1}")
            debug_state(state)
        next_state = step(state)
        state = next_state
        i += 1

    print(f"-- State -- iteration: {i + 1}")
    if debug:
        debug_state(state)
    else:
        print_tokens(state)
        print_mapping(state)


if __name__ == "__main__":
    main()
