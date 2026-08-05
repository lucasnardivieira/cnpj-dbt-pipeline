{{ config(materialized='table') }}

-- Hierarquia oficial do CNAE 2.0: divisao (2 digitos), grupo (3 digitos),
-- classe (5 digitos) e subclasse (codigo completo de 7 digitos). A "secao"
-- (letra A-U) exigiria uma tabela de mapeamento divisao->secao do IBGE que
-- nao faz parte do dataset baixado, por isso nao e derivada aqui.
select
    cnae_fiscal_principal as codigo_cnae,
    left(cnae_fiscal_principal, 2) as divisao,
    left(cnae_fiscal_principal, 3) as grupo,
    left(cnae_fiscal_principal, 5) as classe,
    cnae_fiscal_principal as subclasse,
    count(*) as quantidade_empresas
from {{ ref('int_empresas_ativas') }}
where cnae_fiscal_principal is not null and trim(cnae_fiscal_principal) <> ''
group by 1,2,3,4,5
