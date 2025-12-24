import unittest


class TestMixinsExport(unittest.TestCase):
    def test_webhandler_importable(self):
        from velocity.aws.handlers.mixins import WebHandler

        # ensure the mixin class is exported and callable
        self.assertTrue(callable(WebHandler))
        self.assertIn("WebHandler", WebHandler.__name__)


if __name__ == "__main__":
    unittest.main()
