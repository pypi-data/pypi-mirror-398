from comexdown import tables

BASE_URL = "https://balanca.economia.gov.br/balanca/bd/"


def table(table_name: str) -> str:
    if table_name == "agronegocio":
        return tables.TABLES["agronegocio"]["url"]
    return f"{BASE_URL}tabelas/{tables.AUX_TABLES[table_name]}"


def trade(direction: str, year: int, mun: bool = False, nbm: bool = False) -> str:
    """
    Generates URL for trade data.
    direction: 'exp' or 'imp'
    """
    direction = direction.upper()
    if nbm:
        return f"{BASE_URL}comexstat-bd/nbm/{direction}_{year}_NBM.csv"

    if mun:
        return f"{BASE_URL}comexstat-bd/mun/{direction}_{year}_MUN.csv"

    return f"{BASE_URL}comexstat-bd/ncm/{direction}_{year}.csv"


def complete(direction: str, mun: bool = False) -> str:
    direction = direction.upper()
    if mun:
        return f"{BASE_URL}comexstat-bd/mun/{direction}_COMPLETA_MUN.zip"
    return f"{BASE_URL}comexstat-bd/ncm/{direction}_COMPLETA.zip"
