{% macro padronizar_situacao_cadastral(valor) -%}
    case
        when coalesce(trim(cast({{ valor }} as string)), '') = '01' then 'Ativa'
        when coalesce(trim(cast({{ valor }} as string)), '') = '02' then 'Suspensa'
        when coalesce(trim(cast({{ valor }} as string)), '') = '04' then 'Inativa'
        else 'Outros'
    end
{%- endmacro %}
