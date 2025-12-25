# Example 1/3: MayBe basics
from nofut import MayBe

# Level 1: construction and inspection
just_value = MayBe.just(3)
nothing_value = MayBe.nothing()

assert just_value.is_just()
assert nothing_value.is_nothing()

# Level 2: extraction and defaults
assert just_value.unwrap() == 3
assert nothing_value.or_else(99) == 99

# Level 3: transform and chain
assert just_value.map(lambda x: x + 1).unwrap() == 4
assert (just_value >> (lambda x: MayBe.just(x * 2))).unwrap() == 6

# Level 4: operators and truthiness
assert (nothing_value | 123) == 123
assert bool(just_value)
assert repr(just_value) == "Just(3)"

print("MayBe basics OK")
