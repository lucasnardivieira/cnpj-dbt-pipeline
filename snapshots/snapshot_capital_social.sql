{% snapshot snapshot_capital_social %}

{{
    config(
      target_schema='main',
      unique_key='cnpj_basico',
      strategy='check',
      check_cols=['capital_social']
    )
}}

    select
        cnpj_basico,
        capital_social
    from {{ ref('stg_empresas') }}

{% endsnapshot %}
