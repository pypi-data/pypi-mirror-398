import unittest
from comexdown import urls


class TestUrls(unittest.TestCase):
    def test_trade_ncm_exp(self):
        url = urls.trade(direction="exp", year=2019)
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/EXP_2019.csv",
        )

    def test_trade_ncm_imp(self):
        url = urls.trade(direction="imp", year=2019)
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/IMP_2019.csv",
        )

    def test_trade_mun_exp(self):
        url = urls.trade(direction="exp", year=2019, mun=True)
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/EXP_2019_MUN.csv",
        )

    def test_trade_mun_imp(self):
        url = urls.trade(direction="imp", year=2019, mun=True)
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/IMP_2019_MUN.csv",
        )

    def test_trade_nbm_exp(self):
        url = urls.trade(direction="exp", year=1990, nbm=True)
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/nbm/EXP_1990_NBM.csv",
        )

    def test_trade_nbm_imp(self):
        url = urls.trade(direction="imp", year=1990, nbm=True)
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/nbm/IMP_1990_NBM.csv",
        )

    def test_complete_ncm_exp(self):
        url = urls.complete(direction="exp")
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/EXP_COMPLETA.zip",
        )

    def test_complete_ncm_imp(self):
        url = urls.complete(direction="imp")
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm/IMP_COMPLETA.zip",
        )

    def test_complete_mun_exp(self):
        url = urls.complete(direction="exp", mun=True)
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/EXP_COMPLETA_MUN.zip",
        )

    def test_complete_mun_imp(self):
        url = urls.complete(direction="imp", mun=True)
        self.assertEqual(
            url,
            "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/mun/IMP_COMPLETA_MUN.zip",
        )

    def test_agronegocio(self):
        url = urls.table("agronegocio")
        self.assertEqual(
            url,
            "https://github.com/dankkom/ncm-agronegocio/raw/master/ncm-agronegocio.csv",
        )
