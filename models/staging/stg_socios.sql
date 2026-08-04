select
    cast(cnpj_basico as string) as cnpj_basico,
    cast(identificador_socio as string) as identificador_socio,
    nullif(trim(nome_socio), '') as nome_socio,
    nullif(trim(cnpj_cpf_socio), '') as cnpj_cpf_socio,
    cast(qualificacao_socio as string) as qualificacao_socio,
    nullif(data_entrada_sociedade, '') as data_entrada_sociedade,
    cast(pais as string) as pais,
    nullif(trim(representante_legal), '') as representante_legal,
    nullif(trim(nome_representante), '') as nome_representante,
    cast(qualificacao_representante_legal as string) as qualificacao_representante_legal,
    cast(faixa_etaria as string) as faixa_etaria
from {{ source('raw_cnpj', 'socios') }}
