select
    {{ limpar_cnpj('cnpj_basico') }} as cnpj_basico,
    nullif(trim(razao_social_nome_empresarial), '') as razao_social,
    cast(natureza_juridica as string) as natureza_juridica,
    cast(qualificacao_responsavel as string) as qualificacao_responsavel,
    cast(
        nullif(
            regexp_replace(
                regexp_replace(nullif(trim(capital_social), ''), '\\.', ''),
                ',', '.'
            ),
            ''
        ) as decimal(18, 2)
    ) as capital_social,
    cast(porte_empresa as string) as porte_empresa,
    nullif(trim(ente_federativo_responsavel), '') as ente_federativo_responsavel
from {{ source('raw_cnpj', 'empresas') }}
