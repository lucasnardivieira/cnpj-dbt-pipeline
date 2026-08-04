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

## Status do desafio

Ver [plano_execucao_desafio_franq.md](plano_execucao_desafio_franq.md) para o checklist completo etapa a etapa.
