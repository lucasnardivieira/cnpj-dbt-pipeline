{% macro gerar_coluna_auditoria(modelo_origem) -%}
    current_timestamp as carga_em,
    '{{ modelo_origem }}' as modelo_origem
{%- endmacro %}
