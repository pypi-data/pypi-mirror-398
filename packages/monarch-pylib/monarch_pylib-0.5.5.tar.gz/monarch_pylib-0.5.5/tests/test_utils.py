import unittest
from monarch_pylib.utils import check_dependencies


class TestUtils(unittest.TestCase):

    def test_check_dependencies(self):
        """Test that check_dependencies returns expected structure"""
        result = check_dependencies()

        self.assertIsInstance(result, dict)
        self.assertIn("numpy", result)
        self.assertIn("numba", result)

        for lib_name, lib_info in result.items():
            self.assertIsInstance(lib_info, dict)
            self.assertIn("available", lib_info)
            self.assertIn("version", lib_info)
            self.assertIsInstance(lib_info["available"], bool)

            if lib_info["available"]:
                self.assertIsInstance(lib_info["version"], str)
            else:
                self.assertIsNone(lib_info["version"])

    def test_numpy_available(self):
        """Test that numpy is available"""
        result = check_dependencies()
        self.assertTrue(result["numpy"]["available"])
        self.assertIsNotNone(result["numpy"]["version"])

    def test_numba_available(self):
        """Test that numba is available"""
        result = check_dependencies()
        self.assertTrue(result["numba"]["available"])
        self.assertIsNotNone(result["numba"]["version"])


if __name__ == "__main__":
    unittest.main()
