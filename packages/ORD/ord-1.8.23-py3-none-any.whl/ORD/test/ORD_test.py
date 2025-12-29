import unittest
import ORD


class TestCash(unittest.TestCase):
    def test_connect(self):
        cash = ORD()
        self.assertTrue(cash.open_connect())


if __name__ == '__main__':
    unittest.main()
