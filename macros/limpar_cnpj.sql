{% macro limpar_cnpj(cnpj) -%}
    regexp_replace(regexp_replace(coalesce(cast({{ cnpj }} as string), ''), '[^0-9]', ''), '^0+$', '')
{%- endmacro %}
