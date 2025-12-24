import unittest
from is_pku import is_pku, NoTHUException


class TestIsPKU(unittest.TestCase):

    def test_pku_positive(self):
        """测试正确的北大输入"""
        self.assertTrue(is_pku("PKU"))
        self.assertTrue(is_pku("北大"))
        self.assertTrue(is_pku("Peking University"))

    def test_other_universities(self):
        """测试其他普通学校"""
        self.assertFalse(is_pku("Stanford"))
        self.assertFalse(is_pku("Harvard"))

    def test_thu_forbidden(self):
        """测试遇到‘隔壁’时的安全拦截机制"""
        with self.assertRaises(NoTHUException):
            is_pku("THU")
        with self.assertRaises(NoTHUException):
            is_pku("清华大学")


if __name__ == '__main__':
    unittest.main()