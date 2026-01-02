import unittest
import sys
import os

# Add parent directory to path to import toon_parser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import toon_parser

class TestToonParser(unittest.TestCase):
    def test_primitives(self):
        self.assertEqual(toon_parser.encode(None), "null")
        self.assertEqual(toon_parser.encode(True), "true")
        self.assertEqual(toon_parser.encode(123), "123")
        self.assertEqual(toon_parser.encode("hello"), "hello")
        
    def test_object(self):
        obj = {"name": "Alice", "age": 30}
        encoded = toon_parser.encode(obj)
        self.assertIn("name: Alice", encoded)
        self.assertIn("age: 30", encoded)
        self.assertEqual(toon_parser.decode(encoded), obj)
        
    def test_array(self):
        arr = [1, 2, 3]
        encoded = toon_parser.encode(arr)
        self.assertIn("- 1", encoded)
        self.assertEqual(toon_parser.decode(encoded), arr)

    def test_tabular(self):
        data = [
            {"id": 1, "val": "A"},
            {"id": 2, "val": "B"}
        ]
        encoded = toon_parser.encode(data)
        self.assertIn("id,val", encoded)
        self.assertIn("1,A", encoded)
        self.assertEqual(toon_parser.decode(encoded), data)

    def test_complex(self):
        data = {
            "title": "Trip",
            "items": [
                {"day": 1, "activity": "Lunch"},
                {"day": 2, "activity": "Tour"}
            ]
        }
        encoded = toon_parser.encode(data)
        decoded = toon_parser.decode(encoded)
        self.assertEqual(decoded, data)

if __name__ == '__main__':
    unittest.main()
