# FinOps — Proposta de Produtização no BigQuery

## 1. Contexto e proposta

Este projeto foi desenvolvido localmente com **DuckDB + dbt** para validar a modelagem em camadas (staging → intermediate → marts) sobre uma amostra de ~10.000 linhas por arquivo dos dados públicos de CNPJ da Receita Federal. O objetivo desta seção é propor como o mesmo pipeline seria levado para produção em escala real, usando o **Google BigQuery** como data warehouse.

Em produção, os arquivos completos (~1.2 GB cada, dezenas de milhões de linhas de empresas/estabelecimentos/sócios) seriam:

1. Carregados brutos em uma área de *landing* no BigQuery (ex: `raw_cnpj.estabelecimentos`), via `bq load` ou um job do Cloud Storage → BigQuery (arquivos CSV do governo primeiro copiados para um bucket GCS).
2. Transformados com os mesmos modelos dbt já escritos aqui, trocando apenas o adapter de `dbt-duckdb` para `dbt-bigquery` no `profiles.yml` — a lógica SQL em si muda muito pouco, pois ambos suportam SQL padrão ANSI e Jinja/macros continuam funcionando sem alteração de negócio.
3. Publicados como tabelas/views particionadas e clusterizadas nos datasets `staging`, `intermediate` e `marts`, seguindo a mesma separação de camadas usada localmente.

A principal mudança de arquitetura não está na lógica dos modelos, e sim em **como o BigQuery cobra por consulta** (bytes escaneados) e **como isso deve orientar o design físico das tabelas**, tratado nas seções seguintes.

## 2. Estratégia de Partitioning

O BigQuery cobra por volume de dados escaneado em cada query. Sem particionamento, uma consulta que filtra "empresas abertas nos últimos 30 dias" escanearia a tabela inteira.

**Coluna escolhida: `data_situacao_cadastral` (ou `data_inicio_atividade`, dependendo da tabela).**

- Em `stg_estabelecimentos` / `int_empresas_ativas` / `fct_empresas`: particionar por `DATE(data_situacao_cadastral)`, com `PARTITION BY DATE_TRUNC(data_situacao_cadastral, MONTH)` — os dados da Receita têm baixa granularidade de mudança diária mas alto volume histórico, então partição mensal equilibra número de partições (limite de 4.000 partições por tabela no BigQuery) com poda eficiente.
- Justificativa de negócio: a maioria das análises de FinOps/negócio filtra por período (ex: "empresas abertas em 2024"), e o modelo incremental que já implementamos localmente (`is_incremental()` filtrando por `data_situacao_cadastral`) se traduz diretamente em uma poda de partição no BigQuery — ou seja, a mesma coluna serve tanto para a estratégia incremental do dbt quanto para o particionamento físico da tabela, reduzindo bytes escaneados nas cargas incrementais e nas consultas analíticas.
- Tabelas sem coluna de data confiável (ex: `dim_cnae`, que é pequena e estática) não precisam de particionamento — o custo de escanear a tabela inteira é irrelevante nesse volume.

## 3. Estratégia de Clustering

Clustering no BigQuery reordena fisicamente os dados dentro de cada partição, permitindo poda adicional em filtros e `GROUP BY`/`JOIN` sobre colunas de alta cardinalidade que não fazem sentido como partição.

**Colunas escolhidas, por tabela:**

- `fct_empresas`: cluster por `(uf, cnae_fiscal_principal)`. A maioria das consultas de negócio agrega por estado e por atividade econômica (ex: "quantas empresas ativas de comércio varejista em SP"), e essas duas colunas juntas cobrem os filtros mais comuns sem precisar de índice separado.
- `int_empresas_ativas`: cluster por `cnpj_basico`, já que joins subsequentes (com sócios, com Simples Nacional) sempre passam por essa chave.
- `dim_cnae`: cluster por `codigo_cnae` (chave de join principal com a fato).

Clustering é gratuito para manter (ao contrário de índices tradicionais) e o BigQuery reclusteriza automaticamente em background, então não há custo operacional adicional além de declarar a cláusula `CLUSTER BY` no `config()` do dbt (`cluster_by=['uf', 'cnae_fiscal_principal']`).

## 4. Estimativa conceitual de redução de custo/slots

O BigQuery on-demand cobra ~US$ 6,25 por TB escaneado (valor de referência, sujeito a região/moeda). Para efeito de estimativa conceitual (sem execução real):

- **Sem partition/cluster:** uma query filtrando por UF e por mês em uma tabela de 50 GB escanearia os 50 GB inteiros → custo pleno por execução.
- **Com partition mensal:** se a query filtra 1 mês de um histórico de 24 meses, o BigQuery poda ~23/24 das partições, reduzindo o volume escaneado para ~4% do total antes mesmo de aplicar o filtro de UF.
- **Com clustering adicional por `uf`:** dentro da partição sobrevivente, o clustering permite podar ainda mais blocos que não contêm a UF filtrada — para uma base com 27 UFs distribuídas de forma razoavelmente uniforme, isso pode reduzir o volume remanescente por um fator adicional de ~3 a 5x, dependendo da distribuição real dos dados.
- **Resultado esperado:** uma consulta que escanearia 50 GB sem otimização passaria a escanear algo na casa de poucos GB, o que se traduz em uma fração pequena do custo original — uma redução da ordem de dezenas de vezes é uma expectativa razoável e conservadora para esse padrão de acesso, mas o número exato só pode ser confirmado rodando `EXPLAIN`/dry-run reais contra os dados de produção.
- Para cargas via **slots reservados** (em vez de on-demand), a mesma redução de bytes escaneados se traduz em menos slot-time consumido por query, permitindo atender mais consultas concorrentes com a mesma reserva.

Essa é uma estimativa conceitual para orientar a decisão de design — a validação final exige rodar as queries reais com `--dry_run` no BigQuery para medir bytes processados antes/depois.

## 5. Onboarding — como rodar o projeto do zero

Documentado em detalhe no [README.md](../README.md) principal do repositório. Resumo rápido para um novo colaborador:

1. Clonar o repositório e criar o ambiente virtual (`python -m venv .venv`).
2. Instalar dependências (`pip install dbt-duckdb dbt-utils prefect duckdb pandas`).
3. Rodar `python flows/extract.py` para gerar as amostras locais a partir de `downloaded_files/`.
4. Rodar `dbt run` e `dbt test` (ou `python flows/pipeline.py` para rodar tudo orquestrado via Prefect, com retries).
5. Para a versão BigQuery: trocar o adapter no `profiles.yml` (`type: bigquery`, informando `project`, `dataset` e credenciais de service account), e adicionar as configs de `partition_by`/`cluster_by` nos `config()` dos modelos marts, conforme descrito nas seções 2 e 3 acima.

## 6. Repositório

Link do repositório: (adicionar aqui a URL do GitHub antes do envio final).
