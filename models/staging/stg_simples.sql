select
    cast(cnpj_basico as string) as cnpj_basico,
    nullif(trim(opcao_pelo_simples), '') as opcao_pelo_simples,
    nullif(data_opcao_simples, '') as data_opcao_simples,
    nullif(data_exclusao_simples, '') as data_exclusao_simples,
    nullif(trim(opcao_pelo_mei), '') as opcao_pelo_mei,
    nullif(data_opcao_mei, '') as data_opcao_mei,
    nullif(data_exclusao_mei, '') as data_exclusao_mei
from {{ source('raw_cnpj', 'simples') }}
