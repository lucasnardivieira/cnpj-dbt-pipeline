{{
    config(
        materialized='incremental',
        unique_key='cnpj_basico'
    )
}}

-- Incremental por data_situacao_cadastral: simula carga diaria, reprocessando
-- somente empresas cuja situacao cadastral mudou depois da ultima carga.
select
    cnpj_basico,
    razao_social,
    natureza_juridica,
    porte_empresa,
    capital_social,
    cnae_fiscal_principal,
    uf,
    municipio,
    status_empresa,
    possui_cnae_principal,
    data_situacao_cadastral,
    coalesce(capital_social, 0) as capital_social_limpo,
    {{ gerar_coluna_auditoria('fct_empresas') }}
from {{ ref('int_empresas_ativas') }}
{% if is_incremental() %}
    -- noqa: disable=RF02
    where data_situacao_cadastral > (
        select coalesce(max(data_situacao_cadastral), '00000000') from {{ this }}
    )
    -- noqa: enable=RF02
{% endif %}
