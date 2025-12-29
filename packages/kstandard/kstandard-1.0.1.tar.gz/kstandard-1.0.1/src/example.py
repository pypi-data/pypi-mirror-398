
from kstandard.debug import alert
from kstandard.typing import numeric_t, float2d_t

a: float2d_t = [[1.0, 2.0], [3.0, 4.0]]
b: numeric_t = 3.14

print(f"a: {a}, type: {type(a)}")
print(f"b: {b}, type: {type(b)}")


def something1(x: numeric_t) -> None:
    alert(x)

def something2(x: str) -> None:
    alert(x)


something1(43)
something1("foo")

something2(234)
something2("bar")

