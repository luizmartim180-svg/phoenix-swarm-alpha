import unittest
from core.tidb_client import TiDBClient

class TestBranching(unittest.TestCase):
    def test_tidb_client_connects(self):
        # This test requires env vars; it's a smoke test that will skip if not configured
        import os
        if not os.getenv('TIDB_HOST'):
            self.skipTest('TIDB_HOST not set')
        t = TiDBClient()
        try:
            conn = t.conn
            self.assertIsNotNone(conn)
        finally:
            t.close()

if __name__ == '__main__':
    unittest.main()
