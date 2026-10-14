-- An empty mart passes every column test. This guards against the bug where
-- unaligned samples made every join return 0 rows without any SQL error.
select 1 as no_rows
where not exists (select 1 from {{ ref('fct_empresas') }})
