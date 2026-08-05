# Desafio FRANQ

Este projeto implementa um pipeline de dados com dbt + DuckDB para processar arquivos de CNPJ (Receita Federal) e gerar modelos analiticos em camadas:

- **staging**: normalizacao e limpeza das fontes brutas
- **intermediate**: joins e filtros de negocio
- **marts**: tabelas de negocio prontas para consumo

Orquestracao via Prefect, testes de qualidade via dbt, versionamento de historico (SCD Type 2) via dbt snapshots.

## Pre-requisitos

- Python 3.11+ (testado com 3.12.1)
- Git
- ~15 GB de espaco livre em disco (para os arquivos brutos da Receita Federal)
- Os comandos abaixo sao dados para **Windows (PowerShell)** e **Linux/macOS (bash)**

## Passo a passo para rodar localmente

### 1. Clonar o repositorio

```bash
git clone https://github.com/lucasnardivieira/desafio_franq.git
cd desafio_franq
```

### 2. Baixar os dados brutos da Receita Federal

O repositorio **nao inclui** os arquivos brutos (sao vários GB e estao no `.gitignore`). Baixe o conjunto de dados abertos do CNPJ ("Dados Abertos do CNPJ", Receita Federal), pegando os arquivos zipados por tipo (ex.: `Empresas0.zip`, `Estabelecimentos0.zip`, `Socios0.zip`, `Simples.zip`, `Cnaes.zip`), descompacte e coloque os arquivos dentro da pasta `downloaded_files/` na raiz do projeto, com os nomes originais (internos ao zip):

| Arquivo esperado em `downloaded_files/` | Conteudo |
|---|---|
| `K3241.K03200Y0.D60711.EMPRECSV` | Empresas (parte 0) |
| `K3241.K03200Y0.D60711.ESTABELE` | Estabelecimentos (parte 0) |
| `K3241.K03200Y0.D60711.SOCIOCSV` | Socios (parte 0) |
| `F.K03200$W.SIMPLES.CSV.D60711` | Simples Nacional (arquivo unico, cobre todos os CNPJs) |
| `F.K03200$Z.D60711.CNAECSV` | Tabela de referencia de CNAE |

> Só é necessário baixar a "parte 0" de cada arquivo particionado — o script de amostragem (passo 7) já garante que as amostras geradas se cruzam corretamente entre os arquivos.

### 3. Criar e ativar o ambiente virtual Python

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS (bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

A partir daqui, com o ambiente virtual ativado, os comandos `python` e `dbt` funcionam de forma idêntica nos dois sistemas operacionais (por isso os próximos passos trazem um único bloco de comando).

> Caso a ativação falhe no Windows, use o caminho completo do executável em cada comando, ex.: `.\.venv\Scripts\python.exe` e `.\.venv\Scripts\dbt.exe`.

### 4. Instalar as dependencias Python

```bash
pip install -r requirements.txt
```

Instala `dbt-core`, `dbt-duckdb`, `duckdb`, `pandas` e `prefect` nas versões usadas no projeto.

### 5. Instalar os pacotes dbt (dbt_utils)

```bash
dbt deps --profiles-dir . --project-dir .
```

Lê o `packages.yml` e baixa o pacote `dbt_utils` (usado no teste genérico `expression_is_true`) para `dbt_packages/`.

### 6. Criar o `profiles.yml` (conexao do dbt com o DuckDB)

Esse arquivo é local e não é versionado (contém configuração de ambiente). Crie `profiles.yml` na raiz do projeto com o conteúdo abaixo:

```yaml
franq_desafio:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: 'data/franq.duckdb'
      threads: 4
```

Isso diz ao dbt para usar o adapter DuckDB e persistir o banco no arquivo `data/franq.duckdb`.

### 7. Gerar as amostras de dados

```bash
python flows/extract.py
```

O que esse comando faz:
1. Lê apenas a coluna `cnpj_basico` dos arquivos completos de `EMPRECSV` (empresas) e `ESTABELE` (estabelecimentos), em blocos de 500 mil linhas (sem carregar os arquivos inteiros na memória).
2. Calcula a **interseção** dos `cnpj_basico` distintos entre os dois arquivos, garantindo que exista overlap real entre eles.
3. Sorteia (com seed fixa, reprodutível) uma amostra de 10 mil `cnpj_basico` dentro dessa interseção.
4. Filtra `estabelecimentos`, `empresas`, `socios` e `simples` por esse mesmo conjunto de CNPJs e grava os resultados em `data/sample/*.csv`.
5. Copia a tabela de referência `cnae.csv` por inteiro (é pequena e não tem `cnpj_basico`).

### 8. Rodar o pipeline dbt (staging → intermediate → marts)

```bash
dbt run --profiles-dir . --project-dir .
```

Materializa, na ordem correta de dependências: as views de staging (limpeza), as views intermediate (regras de negócio) e as tabelas de marts (`fct_empresas` incremental e `dim_cnae`).

### 9. Rodar os testes de qualidade de dados

```bash
dbt test --profiles-dir . --project-dir .
```

Executa os 10 testes definidos em `models/schema.yml` (`not_null`, `unique`, `accepted_values`, `relationships`, `dbt_utils.expression_is_true`).

### 10. Rodar o snapshot (histórico SCD Type 2)

```bash
dbt snapshot --profiles-dir . --project-dir .
```

Compara o estado atual de `stg_empresas` com a última versão registrada em `snapshot_capital_social` e cria uma nova linha de histórico sempre que `capital_social` mudar.

### 11. (Opcional) Rodar tudo de uma vez via Prefect

```bash
python flows/pipeline.py
```

Orquestra em sequência os passos 7, 8 e 9 (extração → `dbt run` → `dbt test`), com 1 retry automático por etapa em caso de falha.

### 12. Visualizar os dados gerados

```bash
python ver_dados.py
```

Lista as tabelas/views criadas no DuckDB, mostra a contagem de linhas de cada uma e imprime uma amostra de `fct_empresas` e `dim_cnae`.

## Estrutura

- `flows/extract.py`: gera as amostras CSV a partir dos arquivos brutos (ver passo 7)
- `flows/pipeline.py`: orquestrador Prefect (extração + dbt run + dbt test)
- `models/staging/`: limpeza e normalização das fontes brutas
- `models/intermediate/`: regras de negócio (empresas ativas, 1 linha por empresa)
- `models/marts/`: `fct_empresas` (incremental) e `dim_cnae`
- `macros/`: `limpar_cnpj`, `padronizar_situacao_cadastral`, `gerar_coluna_auditoria`
- `snapshots/`: snapshot SCD2 de evolução do capital social
- `models/schema.yml`: testes de qualidade de dados
- `ver_dados.py`: utilitário para inspecionar rapidamente as tabelas do DuckDB

## Observacoes

- O projeto usa DuckDB como banco local (`data/franq.duckdb`, não versionado).
- A conexão está definida em `profiles.yml` (não versionado, ver passo 6).
- `fct_empresas` é incremental, filtrando por `data_situacao_cadastral` (simula carga diária).
- O snapshot foi criado para monitorar mudanças em `capital_social` ao longo do tempo.

## Evidencia do snapshot (SCD Type 2)

Como a amostra e estatica, simulamos uma mudanca real para provar a captura de historico:

1. Estado inicial: `cnpj_basico = 41277443` com `capital_social = 0,00`.
2. Rodamos `dbt snapshot` (1a vez) -- registro capturado com `dbt_valid_from` e `dbt_valid_to = null`.
3. Alteramos manualmente `capital_social` para `99000,00` em `data/sample/empresas.csv` (simulando mudanca na fonte).
4. Rodamos `dbt snapshot` novamente. Resultado em `snapshot_capital_social`:

| cnpj_basico | capital_social | dbt_valid_from | dbt_valid_to |
|---|---|---|---|
| 41277443 | 0.0 | 2026-08-04 20:06:46 | 2026-08-04 20:07:25 |
| 41277443 | 99000.0 | 2026-08-04 20:07:25 | null |

A linha antiga foi fechada (`dbt_valid_to` preenchido) e uma nova linha foi aberta com o valor atualizado, confirmando que a estrategia `check` (comparando `capital_social`) captura corretamente o historico de mudancas.

## Testes de qualidade

10 testes definidos em [models/schema.yml](models/schema.yml): `not_null`, `unique`, `accepted_values`, `relationships` e `dbt_utils.expression_is_true` (regra de negocio: capital social e quantidade de empresas nunca negativos). Todos os 10 testes rodam com severity `error` (padrao) e passam com dados reais, incluindo o `relationships` entre `stg_socios.cnpj_basico` e `stg_empresas.cnpj_basico`, garantido pela estrategia de amostragem descrita abaixo.

## Bugs encontrados e corrigidos

Durante a revisao final, antes do push, foram encontrados e corrigidos dois bugs que faziam as tabelas mart (`int_empresas_ativas`, `fct_empresas`, `dim_cnae`) ficarem **vazias**, mesmo com `dbt run`/`dbt test` executando sem erro de SQL (o que mostra que ausencia de erro nao garante corretude dos dados -- e preciso validar volume/conteudo real):

1. **Amostragem sem overlap entre arquivos**: `flows/extract.py` amostrava as primeiras N linhas de cada arquivo bruto de forma independente. Como os arquivos de Empresas/Estabelecimentos/Socios nao sao ordenados/alinhados por `cnpj_basico`, o `cnpj_basico` sorteado num arquivo praticamente nunca existia no outro, entao o `inner join` em `int_empresas_ativas` retornava 0 linhas. Corrigido reescrevendo `flows/extract.py` para: (a) ler apenas a coluna `cnpj_basico` dos arquivos completos de empresas e estabelecimentos em chunks (sem carregar tudo em memoria), (b) calcular a intersecao dos `cnpj_basico` distintos entre os dois arquivos, (c) sortear uma amostra determinística de 10 mil `cnpj_basico` dessa intersecao (seed fixa), e (d) filtrar todos os demais arquivos (estabelecimentos, empresas, socios, simples) por esse mesmo conjunto de CNPJs, garantindo overlap real entre as amostras.
2. **Filtro de `situacao_cadastral` com valores incompativeis**: `int_empresas_ativas.sql` comparava `situacao_cadastral` com os codigos brutos (`'01'`, `'02'`, `'04'`), mas a coluna ja havia sido transformada em rotulos textuais (`'Ativa'`, `'Suspensa'`, `'Inativa'`) pela macro `padronizar_situacao_cadastral()` aplicada em `stg_estabelecimentos`. O filtro nunca dava match. Corrigido para comparar contra os rotulos textuais.

Um terceiro ajuste, motivado pela correcao acima, foi necessario: com overlap real, uma mesma empresa (`cnpj_basico`) pode ter multiplas filiais em `estabelecimentos`, o que multiplicava linhas no join e quebrava o teste `unique` em `fct_empresas`. Adicionamos um `qualify row_number()` em `int_empresas_ativas.sql` para manter 1 linha por empresa, priorizando a matriz (`identificador_matriz_filial = '1'`).

