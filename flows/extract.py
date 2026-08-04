from pathlib import Path
import random

import pandas as pd


SOURCE_DIR = Path(__file__).resolve().parent.parent / "downloaded_files"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
SAMPLE_ROWS = 10_000
CHUNK_SIZE = 500_000
SEED = 42

EMPRESAS_FILE = "K3241.K03200Y0.D60711.EMPRECSV"
ESTABELECIMENTOS_FILE = "K3241.K03200Y0.D60711.ESTABELE"

FILES = [
    (
        ESTABELECIMENTOS_FILE,
        "estabelecimentos.csv",
        [
            "cnpj_basico",
            "cnpj_ordem",
            "cnpj_dv",
            "identificador_matriz_filial",
            "nome_fantasia",
            "situacao_cadastral",
            "data_situacao_cadastral",
            "motivo_situacao_cadastral",
            "nome_cidade_exterior",
            "pais",
            "data_inicio_atividade",
            "cnae_fiscal_principal",
            "cnae_fiscal_secundaria",
            "tipo_logradouro",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cep",
            "uf",
            "municipio",
            "ddd_1",
            "telefone_1",
            "ddd_2",
            "telefone_2",
            "ddd_fax",
            "fax",
            "correio_eletronico",
            "situacao_especial",
            "data_situacao_especial",
        ],
    ),
    (
        EMPRESAS_FILE,
        "empresas.csv",
        [
            "cnpj_basico",
            "razao_social_nome_empresarial",
            "natureza_juridica",
            "qualificacao_responsavel",
            "capital_social",
            "porte_empresa",
            "ente_federativo_responsavel",
        ],
    ),
    (
        "K3241.K03200Y0.D60711.SOCIOCSV",
        "socios.csv",
        [
            "cnpj_basico",
            "identificador_socio",
            "nome_socio",
            "cnpj_cpf_socio",
            "qualificacao_socio",
            "data_entrada_sociedade",
            "pais",
            "representante_legal",
            "nome_representante",
            "qualificacao_representante_legal",
            "faixa_etaria",
        ],
    ),
    (
        "F.K03200$W.SIMPLES.CSV.D60711",
        "simples.csv",
        [
            "cnpj_basico",
            "opcao_pelo_simples",
            "data_opcao_simples",
            "data_exclusao_simples",
            "opcao_pelo_mei",
            "data_opcao_mei",
            "data_exclusao_mei",
        ],
    ),
]

CNAE_FILE = ("F.K03200$Z.D60711.CNAECSV", "cnae.csv", ["codigo", "descricao"])


def coletar_cnpjs_distintos(caminho: str, encoding: str = "latin-1", sep: str = ";") -> set[str]:
    """Le apenas a 1a coluna (cnpj_basico) em chunks, sem carregar o arquivo inteiro."""
    cnpjs: set[str] = set()
    for chunk in pd.read_csv(
        caminho, encoding=encoding, sep=sep, header=None,
        usecols=[0], dtype=str, chunksize=CHUNK_SIZE, low_memory=False,
    ):
        cnpjs.update(chunk[0].dropna().unique())
    return cnpjs


def filtrar_por_cnpj(caminho: str, colunas: list[str], cnpjs_alvo: set[str], encoding: str = "latin-1", sep: str = ";") -> pd.DataFrame:
    partes = []
    for chunk in pd.read_csv(
        caminho, encoding=encoding, sep=sep, header=None,
        dtype=str, chunksize=CHUNK_SIZE, low_memory=False,
    ):
        chunk.columns = colunas
        partes.append(chunk[chunk["cnpj_basico"].isin(cnpjs_alvo)])
    if not partes:
        return pd.DataFrame(columns=colunas)
    return pd.concat(partes, ignore_index=True)


def selecionar_amostra_cnpjs(n: int = SAMPLE_ROWS) -> set[str]:
    """Garante overlap real: sorteia cnpj_basico que existem em empresas E estabelecimentos."""
    print("Coletando cnpj_basico de empresas...")
    cnpjs_empresas = coletar_cnpjs_distintos(str(SOURCE_DIR / EMPRESAS_FILE))
    print(f"  {len(cnpjs_empresas)} cnpj_basico distintos")

    print("Coletando cnpj_basico de estabelecimentos...")
    cnpjs_estabelecimentos = coletar_cnpjs_distintos(str(SOURCE_DIR / ESTABELECIMENTOS_FILE))
    print(f"  {len(cnpjs_estabelecimentos)} cnpj_basico distintos")

    overlap = sorted(cnpjs_empresas & cnpjs_estabelecimentos)
    print(f"Overlap empresas x estabelecimentos: {len(overlap)} cnpj_basico em comum")

    random.seed(SEED)
    amostra = set(random.sample(overlap, min(n, len(overlap))))
    print(f"Amostra selecionada: {len(amostra)} cnpj_basico (seed={SEED})")
    return amostra


if __name__ == "__main__":
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    amostra_cnpjs = selecionar_amostra_cnpjs(SAMPLE_ROWS)

    for source_name, target_name, colunas in FILES:
        source_path = SOURCE_DIR / source_name
        target_path = SAMPLE_DIR / target_name
        if not source_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {source_path}")
        df = filtrar_por_cnpj(str(source_path), colunas, amostra_cnpjs)
        df.to_csv(target_path, index=False)
        print(f"Gerada amostra: {target_path.name} ({len(df)} linhas)")

    cnae_source, cnae_target, cnae_colunas = CNAE_FILE
    cnae_source_path = SOURCE_DIR / cnae_source
    cnae_target_path = SAMPLE_DIR / cnae_target
    if not cnae_source_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {cnae_source_path}")
    df_cnae = pd.read_csv(
        cnae_source_path, encoding="latin-1", sep=";", header=None,
        dtype=str, low_memory=False,
    )
    df_cnae.columns = cnae_colunas
    df_cnae.to_csv(cnae_target_path, index=False)
    print(f"Gerada amostra: {cnae_target_path.name} ({len(df_cnae)} linhas, tabela de referencia completa)")
