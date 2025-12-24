import unittest

from bounce_desktop import Desktop


class TestDesktop(unittest.TestCase):
    def test_get_frame(self):
        d = Desktop.create(300, 200)
        frame = d.get_frame()
        self.assertEqual(frame.shape, (200, 300, 4))
        self.assertTrue("DISPLAY" in d.get_desktop_env())


if __name__ == "__main__":
    unittest.main()
