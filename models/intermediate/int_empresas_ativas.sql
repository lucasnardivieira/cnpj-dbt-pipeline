{{ config(materialized='view') }}

-- Uma empresa (cnpj_basico) pode ter varias filiais em estabelecimentos; para manter
-- granularidade de 1 linha por empresa, priorizamos a matriz (identificador_matriz_filial = '1')
-- e desempatamos de forma deterministica via qualify.
select
    e.cnpj_basico,
    e.razao_social,
    e.natureza_juridica,
    e.capital_social,
    e.porte_empresa,
    est.cnae_fiscal_principal,
    est.uf,
    est.municipio,
    est.situacao_cadastral,
    est.data_situacao_cadastral,
    est.identificador_matriz_filial,
    case
        when est.situacao_cadastral in ('Ativa', 'Suspensa', 'Inativa') then 'ativa'
        else 'inativa'
    end as status_empresa,
    case
        when est.cnae_fiscal_principal is not null and trim(est.cnae_fiscal_principal) <> '' then true
        else false
    end as possui_cnae_principal
from {{ ref('stg_empresas') }} as e
inner join {{ ref('stg_estabelecimentos') }} as est
    on e.cnpj_basico = est.cnpj_basico
where est.situacao_cadastral in ('Ativa', 'Suspensa', 'Inativa')
qualify row_number() over (
    partition by e.cnpj_basico
    order by case when est.identificador_matriz_filial = '1' then 0 else 1 end, est.cnpj_ordem
) = 1
