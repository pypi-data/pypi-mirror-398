import unittest
from nofut import Result


class TestResult(unittest.TestCase):

    def test_static_constructors(self):
        ok = Result.ok(42)
        self.assertTrue(ok.is_ok())
        self.assertFalse(ok.is_err())
        self.assertEqual(ok.unwrap(), 42)

        err = Result.err("error message")
        self.assertTrue(err.is_err())
        self.assertFalse(err.is_ok())

    def test_err_with_code(self):
        err = Result.err("not found", code="NOT_FOUND")
        self.assertTrue(err.is_err())
        msg, code, details = err.unwrap_err()
        self.assertEqual(msg, "not found")
        self.assertEqual(code, "NOT_FOUND")
        self.assertIsNone(details)

    def test_err_with_details(self):
        err = Result.err("validation", code="INVALID", details={"field": "name"})
        msg, code, details = err.unwrap_err()
        self.assertEqual(msg, "validation")
        self.assertEqual(code, "INVALID")
        self.assertEqual(details, {"field": "name"})

    def test_err_message_only(self):
        err = Result.err("simple error")
        msg, code, details = err.unwrap_err()
        self.assertEqual(msg, "simple error")
        self.assertIsNone(code)
        self.assertIsNone(details)

    def test_unwrap_errors(self):
        ok = Result.ok(42)
        err = Result.err("error")

        with self.assertRaises(ValueError):
            err.unwrap()

        with self.assertRaises(ValueError):
            ok.unwrap_err()

    def test_unwrap_or(self):
        ok = Result.ok("success")
        self.assertEqual(ok.unwrap_or("fallback"), "success")

        err = Result.err("error")
        self.assertEqual(err.unwrap_or("fallback"), "fallback")

    def test_map_on_ok(self):
        ok = Result.ok(5)
        r2 = ok.map(lambda x: x + 3)
        self.assertTrue(isinstance(r2, Result))
        self.assertTrue(r2.is_ok())
        self.assertEqual(r2.unwrap(), 8)

    def test_map_on_err(self):
        err = Result.err("error")
        r2 = err.map(lambda x: x * 2)
        self.assertTrue(isinstance(r2, Result))
        self.assertTrue(r2.is_err())

    def test_map_err_on_err(self):
        err = Result.err("error", code="CODE")
        r2 = err.map_err(lambda msg, code, details: (f"wrapped: {msg}", code, details))
        self.assertTrue(r2.is_err())
        msg, code, _ = r2.unwrap_err()
        self.assertEqual(msg, "wrapped: error")
        self.assertEqual(code, "CODE")

    def test_map_err_on_ok(self):
        ok = Result.ok(42)
        r2 = ok.map_err(lambda msg, code, details: (f"wrapped: {msg}", code, details))
        self.assertTrue(r2.is_ok())
        self.assertEqual(r2.unwrap(), 42)

    def test_map_propagates_exceptions(self):
        ok = Result.ok(1)
        with self.assertRaises(ZeroDivisionError):
            ok.map(lambda x: x / 0)

    def test_flat_map_on_ok(self):
        ok = Result.ok(10)
        r = ok.flat_map(lambda x: Result.ok(x * 2))
        self.assertTrue(r.is_ok())
        self.assertEqual(r.unwrap(), 20)

    def test_flat_map_on_err(self):
        err = Result.err("error")
        r = err.flat_map(lambda x: Result.ok(x * 2))
        self.assertTrue(r.is_err())

    def test_flat_map_returns_err(self):
        ok = Result.ok(5)
        r = ok.flat_map(lambda x: Result.err("oops"))
        self.assertTrue(r.is_err())

    def test_flat_map_invalid_return_type(self):
        ok = Result.ok(3)
        with self.assertRaises(TypeError):
            ok.flat_map(lambda x: x * 2)

    def test_and_then_alias(self):
        ok = Result.ok(10)
        r = ok.and_then(lambda x: Result.ok(x * 2))
        self.assertTrue(r.is_ok())
        self.assertEqual(r.unwrap(), 20)

    def test_rshift_operator(self):
        ok = Result.ok(10)
        r = ok >> (lambda x: Result.ok(x * 2))
        self.assertTrue(isinstance(r, Result))
        self.assertEqual(r.unwrap(), 20)

        # chainage
        r2 = ok >> (lambda x: Result.ok(x + 1)) >> (lambda x: Result.ok(x * 3))
        self.assertEqual(r2.unwrap(), (10 + 1) * 3)

        # >> sur Err reste Err
        err = Result.err("error")
        e2 = err >> (lambda x: Result.ok(x + 1))
        self.assertTrue(e2.is_err())

    def test_or_operator(self):
        ok = Result.ok(7)
        self.assertEqual(ok | 100, 7)

        err = Result.err("error")
        self.assertEqual(err | 100, 100)

    def test_bool_truthiness(self):
        ok = Result.ok("x")
        err = Result.err("error")
        self.assertTrue(bool(ok))
        self.assertFalse(bool(err))

    def test_repr(self):
        self.assertEqual(repr(Result.ok(42)), "Ok(42)")
        self.assertEqual(repr(Result.err("fail")), "Err('fail')")
        self.assertEqual(repr(Result.err("fail", code="CODE")), "Err('fail', code='CODE')")

    def test_to_dict_ok(self):
        ok = Result.ok(42)
        d = ok.to_dict()
        self.assertEqual(d, {"ok": True, "value": 42})

    def test_to_dict_ok_complex(self):
        ok = Result.ok({"name": "test", "id": 1})
        d = ok.to_dict()
        self.assertEqual(d, {"ok": True, "value": {"name": "test", "id": 1}})

    def test_to_dict_err_simple(self):
        err = Result.err("not found")
        d = err.to_dict()
        self.assertEqual(d, {"ok": False, "error": "not found"})

    def test_to_dict_err_with_code(self):
        err = Result.err("not found", code="NOT_FOUND")
        d = err.to_dict()
        self.assertEqual(d, {"ok": False, "error": "not found", "code": "NOT_FOUND"})

    def test_to_dict_err_full(self):
        err = Result.err("validation", code="INVALID", details={"field": "name"})
        d = err.to_dict()
        self.assertEqual(d, {
            "ok": False,
            "error": "validation",
            "code": "INVALID",
            "details": {"field": "name"}
        })

    def test_store_none_in_ok(self):
        ok = Result.ok(None)
        self.assertTrue(ok.is_ok())
        self.assertIsNone(ok.unwrap())

    def test_chained_operations(self):
        def safe_div(a, b):
            if b == 0:
                return Result.err("division by zero", code="DIV_ZERO")
            return Result.ok(a / b)

        result = (
            Result.ok(10)
            >> (lambda x: safe_div(x, 2))
            >> (lambda x: safe_div(x, 5))
        )
        self.assertTrue(result.is_ok())
        self.assertEqual(result.unwrap(), 1.0)

        result_err = (
            Result.ok(10)
            >> (lambda x: safe_div(x, 0))
            >> (lambda x: safe_div(x, 5))
        )
        self.assertTrue(result_err.is_err())
        msg, code, _ = result_err.unwrap_err()
        self.assertEqual(msg, "division by zero")
        self.assertEqual(code, "DIV_ZERO")


if __name__ == "__main__":
    unittest.main()
