from pathlib import Path
import pandas as pd


SOURCE_DIR = Path(__file__).resolve().parent.parent / "downloaded_files"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
SAMPLE_ROWS = 10_000

FILES = [
    (
        "K3241.K03200Y0.D60711.ESTABELE",
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
        "K3241.K03200Y0.D60711.EMPRECSV",
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
    (
        "F.K03200$Z.D60711.CNAECSV",
        "cnae.csv",
        ["codigo", "descricao"],
    ),
]


def gerar_amostra(caminho_csv: str, caminho_saida: str, colunas: list[str], n: int = SAMPLE_ROWS, encoding: str = "latin-1", sep: str = ";") -> str:
    df = pd.read_csv(caminho_csv, encoding=encoding, sep=sep, nrows=n, header=None, low_memory=False, dtype=str)
    df.columns = colunas
    df.to_csv(caminho_saida, index=False, header=True)
    return caminho_saida


if __name__ == "__main__":
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    for source_name, target_name, colunas in FILES:
        source_path = SOURCE_DIR / source_name
        target_path = SAMPLE_DIR / target_name
        if not source_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {source_path}")
        gerar_amostra(str(source_path), str(target_path), colunas, n=SAMPLE_ROWS)
        print(f"Gerada amostra: {target_path.name} ({SAMPLE_ROWS} linhas)")
