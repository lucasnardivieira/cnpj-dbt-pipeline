# Desafio FRANQ

Este projeto implementa um pipeline de dados com dbt + DuckDB para processar arquivos de CNPJ e gerar modelos analiticos em camadas:

- staging: normalizacao e limpeza das fontes brutas
- intermediate: joins e filtros de negocio
- marts: tabelas de negocio prontas para consumo

## Como executar

1. Ative o ambiente virtual:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. Gere as amostras locais:
   ```powershell
   python flows/extract.py
   ```
3. Execute o pipeline dbt:
   ```powershell
   .\.venv\Scripts\dbt.exe run --profiles-dir . --project-dir .
   ```
4. Execute os testes:
   ```powershell
   .\.venv\Scripts\dbt.exe test --profiles-dir . --project-dir .
   ```
5. Execute o snapshot:
   ```powershell
   .\.venv\Scripts\dbt.exe snapshot --profiles-dir . --project-dir .
   ```
6. Execute o fluxo Prefect (orquestra os passos 2 a 4):
   ```powershell
   python flows/pipeline.py
   ```

## Estrutura

- flows/extract.py: gera amostras CSV a partir dos arquivos baixados
- flows/pipeline.py: orquestrador Prefect com extracao, dbt run e dbt test
- models/staging: limpeza e normalizacao das fontes brutas
- models/intermediate: regras de negocio (empresas ativas)
- models/marts: fct_empresas (incremental) e dim_cnae
- macros/: limpar_cnpj, padronizar_situacao_cadastral, gerar_coluna_auditoria
- snapshots/: snapshot SCD2 de evolucao do capital social
- models/schema.yml: testes de qualidade de dados
- docs/finops_bigquery.md: proposta de produtizacao no BigQuery (partitioning/clustering/custos)

## Observacoes

- O projeto usa DuckDB como banco local.
- A conexao esta definida em profiles.yml (nao versionado).
- fct_empresas e incremental, filtrando por data_situacao_cadastral (simula carga diaria).
- O snapshot foi criado para monitorar mudancas em capital_social ao longo do tempo.

## Evidencia do snapshot (SCD Type 2)

Como a amostra e estatica, simulamos uma mudanca real para provar a captura de historico:

1. Estado inicial: `cnpj_basico = 41273589` com `capital_social = 5000,00`.
2. Rodamos `dbt snapshot` (1a vez) -- registro capturado com `dbt_valid_from` e `dbt_valid_to = null`.
3. Alteramos manualmente `capital_social` para `99000,00` em `data/sample/empresas.csv` (simulando mudanca na fonte).
4. Rodamos `dbt snapshot` novamente. Resultado em `snapshot_capital_social`:

| cnpj_basico | capital_social | dbt_valid_from | dbt_valid_to |
|---|---|---|---|
| 41273589 | 5000.0 | 2026-08-02 19:04:09 | 2026-08-04 19:12:50 |
| 41273589 | 99000.0 | 2026-08-04 19:12:50 | null |

A linha antiga foi fechada (`dbt_valid_to` preenchido) e uma nova linha foi aberta com o valor atualizado, confirmando que a estrategia `check` (comparando `capital_social`) captura corretamente o historico de mudancas.

## Testes de qualidade

10 testes definidos em [models/schema.yml](models/schema.yml): `not_null`, `unique`, `accepted_values`, `relationships` e `dbt_utils.expression_is_true` (regra de negocio: capital social e quantidade de empresas nunca negativos).

O teste `relationships` entre `stg_socios.cnpj_basico` e `stg_empresas.cnpj_basico` esta configurado com `severity: warn` e documentado propositalmente: as amostras de socios e empresas sao as primeiras ~10 mil linhas de arquivos brutos diferentes e independentes, sem garantia de overlap de CNPJ. Em producao, com o dataset completo, esse teste deveria voltar a severity `error`.

## Status do desafio

Ver [plano_execucao_desafio_franq.md](plano_execucao_desafio_franq.md) para o checklist completo etapa a etapa.
