# Example 3/3: Result pipelines and error handling
from nofut import Result

# Level 1: constructors and checks
ok_value = Result.ok(42)
err_not_found = Result.err("not found", code="NOT_FOUND")
err_details = Result.err("validation", code="INVALID", details={"field": "name"})

assert ok_value.is_ok()
assert err_not_found.is_err()

# Level 2: unwrap and defaults
assert ok_value.unwrap() == 42
assert ok_value.unwrap_or(0) == 42
assert err_not_found.unwrap_or(0) == 0

msg, code, details = err_not_found.unwrap_err()
assert (msg, code, details) == ("not found", "NOT_FOUND", None)

# Level 3: map and map_err
assert ok_value.map(lambda x: x + 1).unwrap() == 43
assert err_not_found.map(lambda x: x + 1).is_err()

transformed = err_not_found.map_err(lambda m, c, d: (f"Error: {m}", c, d))
msg2, _, _ = transformed.unwrap_err()
assert msg2 == "Error: not found"

# Level 4: chaining and operators
assert (ok_value >> (lambda x: Result.ok(x * 2))).unwrap() == 84
assert (ok_value.and_then(lambda x: Result.ok(x * 2))).unwrap() == 84
assert (err_not_found >> (lambda x: Result.ok(x * 2))).is_err()

assert (ok_value | 0) == 42
assert (err_not_found | 0) == 0
assert bool(ok_value)
assert not bool(err_not_found)


# Level 5: practical pipeline

def parse_int(s: str) -> Result:
    try:
        return Result.ok(int(s))
    except ValueError:
        return Result.err(f"'{s}' is not an int", code="PARSE_ERROR")


def safe_div(a: int, b: int) -> Result:
    if b == 0:
        return Result.err("division by zero", code="DIV_ZERO")
    return Result.ok(a / b)


def compute(a_str: str, b_str: str) -> Result:
    return parse_int(a_str) >> (
        lambda a: parse_int(b_str) >> (lambda b: safe_div(a, b))
    )


r1 = compute("10", "2")
assert r1.is_ok() and r1.unwrap() == 5.0

r2 = compute("10", "0")
assert r2.is_err()
_, code, _ = r2.unwrap_err()
assert code == "DIV_ZERO"

r3 = compute("abc", "2")
assert r3.is_err()
_, code, _ = r3.unwrap_err()
assert code == "PARSE_ERROR"


# Level 6: to_dict for API responses

def handle_request(data: dict) -> dict:
    return parse_int(data.get("value", "")).map(lambda x: x * 2).to_dict()


assert handle_request({"value": "21"}) == {"ok": True, "value": 42}
assert handle_request({"value": "bad"}) == {
    "ok": False,
    "error": "'bad' is not an int",
    "code": "PARSE_ERROR",
}

# Details are preserved
assert err_details.to_dict() == {
    "ok": False,
    "error": "validation",
    "code": "INVALID",
    "details": {"field": "name"},
}


# Level 7: add context with map_err

def add_context(msg, code, details):
    return (f"[compute] {msg}", code, details)


r4 = compute("x", "5").map_err(add_context)
msg, _, _ = r4.unwrap_err()
assert msg == "[compute] 'x' is not an int"

print("Result examples OK")
