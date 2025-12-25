import unittest


def test():
    loader = unittest.TestLoader()
    tests = loader.discover(start_dir="petrus.tests")
    runner = unittest.TextTestRunner()
    result = runner.run(tests)
    return result
