import unittest
from schwifty import IBAN

_iban_1 = 'DE43500105175451887913'
_bic_expected = 'INGDDEFFXXX'


class IbanTestCase(unittest.TestCase):
    def test_iban_decoding(self):
        _ib_1: IBAN = IBAN(_iban_1)
        self.assertIsNotNone(_ib_1)
        _bank_code = _ib_1.bank_code
        self.assertIsNotNone(_bank_code)
        _account_code = _ib_1.account_code
        self.assertIsNotNone(_account_code)
        _country_code = _ib_1.country_code
        self.assertIsNotNone(_country_code)
        _bic = _ib_1.bic
        self.assertIsNotNone(_bic)
        self.assertEqual(_bic, _bic_expected)


if __name__ == '__main__':
    unittest.main()
