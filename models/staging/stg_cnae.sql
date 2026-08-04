select
    cast(codigo as string) as codigo,
    nullif(trim(descricao), '') as descricao
from {{ source('raw_cnpj', 'cnae') }}
