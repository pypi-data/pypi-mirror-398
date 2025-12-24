import unittest

from velocity.aws.handlers import context as handler_context


class TestTrackingSanitization(unittest.TestCase):
    def test_truncate_and_strip_control_chars(self):
        raw_notes = "  hello\nworld\x00" + "a" * 5000
        sanitized = handler_context.sanitize_tracking_payload({"notes": raw_notes})
        self.assertIn("...[TRUNCATED]", sanitized["notes"])
        self.assertNotIn("\x00", sanitized["notes"])

    def test_payload_prunes_when_over_limit(self):
        payload = {"notes": "note", "path": "/test"}
        for i in range(50):
            payload[f"field_{i}"] = "x" * 400
        sanitized = handler_context.sanitize_tracking_payload(payload)
        self.assertTrue(sanitized.get("payload_truncated"))
        allowed = set(handler_context._TRACKING_PRIORITIZED_KEYS) | {"payload_truncated"}
        self.assertTrue(set(sanitized.keys()).issubset(allowed))

    def test_tracking_table_name_matches_hash(self):
        table = handler_context.tracking_table_name_for_email("User@Example.com")
        self.assertTrue(table.startswith("user_tracking.cc_"))
        self.assertTrue(table.islower())


if __name__ == "__main__":
    unittest.main()
