{{ config(materialized='table') }}

select
    cnae_fiscal_principal as codigo_cnae,
    left(cnae_fiscal_principal, 2) as secao,
    left(cnae_fiscal_principal, 4) as divisao,
    left(cnae_fiscal_principal, 6) as grupo,
    cnae_fiscal_principal as classe,
    count(*) as quantidade_empresas
from {{ ref('int_empresas_ativas') }}
where cnae_fiscal_principal is not null and trim(cnae_fiscal_principal) <> ''
group by 1,2,3,4,5
