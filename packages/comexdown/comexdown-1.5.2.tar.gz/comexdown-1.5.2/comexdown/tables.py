TABLES = {
    "ncm": {
        "description": "Códigos NCM e descrições.",
        "file_ref": "NCM.csv",
        "pkey": ["CO_NCM"],
        "name": "NCM - Nomenclatura Comum do Mercosul",
    },
    "sh": {
        "description": (
            "Códigos e descrições do Sistema Harmonizado (Seções, "
            "Capítulos-SH2, Posições-SH4 e Subposições-SH6)."
        ),
        "file_ref": "NCM_SH.csv",
        "pkey": ["CO_SH6"],
        "name": "SH - Sistema Harmonizado",
    },
    "cuci": {
        "description": (
            "Códigos e descrições dos níveis da classificação CUCI "
            "(Revisão 4). Pode ser utilizada conjuntamente com ISIC."
        ),
        "file_ref": "NCM_CUCI.csv",
        "pkey": ["CO_CUCI_ITEM"],
        "name": "CUCI - Classificação Uniforme para Comércio Internacional",
    },
    "cgce": {
        "description": (
            "Códigos e descrições dos níveis da classificação CGCE."
        ),
        "file_ref": "NCM_CGCE.csv",
        "pkey": ["CO_CGCE_N3"],
        "name": "CGCE - Classificação por Grandes Categorias Econômicas",
    },
    "isic": {
        "description": (
            "Códigos e descrições da classificação ISIC (Revisão 4)."
        ),
        "file_ref": "NCM_ISIC.csv",
        "pkey": ["CO_ISIC_CLASSE"],
        "name": (
            "ISIC - International Standard Industrial Classification "
            "(Setores Industriais)"
        ),
    },
    "siit": {
        "description": "Códigos e descrições da classificação SIIT.",
        "file_ref": "NCM_SIIT.csv",
        "pkey": ["CO_SIIT"],
        "name": "SIIT - Setores Industriais por Intensidade Tecnológica",
    },
    "fat_agreg": {
        "description": (
            "Códigos e descrições de Fator Agregado das NCMs. Pode ser "
            "utilizada conjuntamente com a tabela de PPI ou PPE."
        ),
        "file_ref": "NCM_FAT_AGREG.csv",
        "pkey": ["CO_FAT_AGREG"],
        "name": "Fator Agregado da NCM - Classificação própria da SECEX",
    },
    "unidade": {
        "description": (
            "Códigos e descrições das unidades estatísticas das NCMs."
        ),
        "file_ref": "NCM_UNIDADE.csv",
        "pkey": ["CO_UNID"],
        "name": "Unidade Estatística da NCM",
    },
    "ppi": {
        "description": (
            "Códigos e descrições da Pauta de Produtos Importados. DEVE SER "
            "UTILIZADA APENAS PARA IMPORTAÇÃO."
        ),
        "file_ref": "NCM_PPI.csv",
        "pkey": ["CO_PPI"],
        "name": (
            "Pauta de Produtos Importados - Classificação própria da SECEX"
        ),
    },
    "ppe": {
        "description": (
            "Códigos e descrições da Pauta de Produtos Exportados. DEVE SER "
            "UTILIZADA APENAS PARA EXPORTAÇÃO."
        ),
        "file_ref": "NCM_PPE.csv",
        "pkey": ["CO_PPE"],
        "name": (
            "Pauta de Produtos Exportados - Classificação própria da SECEX"
        ),
    },
    "grupo": {
        "description": (
            "Códigos e descrições de Grupo de Produtos. DEVE SER UTILIZADA "
            "APENAS PARA EXPORTAÇÃO."
        ),
        "file_ref": "NCM_GRUPO.csv",
        "pkey": ["CO_EXP_SUBSET"],
        "name": "Grupo de Produtos- Classificação própria da SECEX",
    },
    "pais": {
        "description": "Códigos e descrições de países.",
        "file_ref": "PAIS.csv",
        "pkey": ["CO_PAIS"],
        "name": "Países",
    },
    "pais_bloco": {
        "description": (
            "Códigos e descrições das principais agregações de países em "
            "blocos. Deve ser usada em cojunto com a tabela de países."
        ),
        "file_ref": "PAIS_BLOCO.csv",
        "pkey": ["CO_BLOCO"],
        "name": "Blocos de Países",
    },
    "uf": {
        "description": (
            "Códigos e nome das unidades da federação (estados) do Brasil."
        ),
        "file_ref": "UF.csv",
        "pkey": ["CO_UF"],
        "name": "Unidades da Federação",
    },
    "uf_mun": {
        "description": (
            "Códigos e nome dos municípios brasileiros. Pode ser utilizada em "
            "conjunto com a tabela de UF. Fundamental para utilização junto "
            "com o arquivo de dados brutos por municípios domicílio fiscal "
            "das empresas."
        ),
        "file_ref": "UF_MUN.csv",
        "pkey": ["CO_MUN_GEO"],
        "name": "Municípios",
    },
    "via": {
        "description": "Código e descrição da via (modal) de transporte",
        "file_ref": "VIA.csv",
        "pkey": ["CO_VIA"],
        "name": "Via",
    },
    "urf": {
        "description": (
            "Código e descrição da Unidade da Receita Federal "
            "(embarque/despacho)."
        ),
        "file_ref": "URF.csv",
        "pkey": ["CO_URF"],
        "name": "Urf",
    },
    "isic_cuci": {
        "description": (
            "Códigos e descrições dos níveis ISIC e CUCI usados na coletiva "
            "de apresentação da balança comercial brasileira."
        ),
        "file_ref": "ISIC_CUCI.csv",
        "pkey": [],
        "name": "ISIC Seção x CUCI Grupo",
    },
    "nbm": {
        "description": "Códigos NBM e descrições.",
        "file_ref": "NBM.csv",
        "pkey": ["CO_NBM"],
        "name": "NBM (1989-1996) - Nomenclatura Brasileira de Mercadorias",
    },
    "nbm_ncm": {
        "description": "Tabela de conversão entre códigos NBM e NCM.",
        "file_ref": "NBM_NCM.csv",
        "pkey": [],
        "name": "NBMxNCM - Tabela de conversão",
    },
    "agronegocio": {
        "description": "Tabela com códigos NCM do agronegócio brasileiro.",
        "file_ref": "ncm-agronegocio.csv",
        "pkey": ["CO_NCM"],
        "name": "NCM Agronegócio",
        "url": (
            "https://github.com/dankkom/ncm-agronegocio/raw"
            "/master/ncm-agronegocio.csv"
        ),
    },
}

AUX_TABLES = {
    name: TABLES[name]["file_ref"] for name in TABLES
}
