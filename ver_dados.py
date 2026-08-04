import duckdb
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

con = duckdb.connect('data/franq.duckdb', read_only=True)

print("Tabelas disponiveis:")
print(con.sql("show tables").df())

print("\nContagem de linhas por tabela/view:")
for t in ["stg_empresas", "stg_estabelecimentos", "stg_socios", "stg_simples",
          "int_empresas_ativas", "fct_empresas", "dim_cnae"]:
    n = con.sql(f"select count(*) as n from main.{t}").fetchone()[0]
    print(f"  {t}: {n}")

print("\nAmostra de fct_empresas:")
print(con.sql("select * from main.fct_empresas limit 10").df())

print("\nTop 5 CNAEs por quantidade de empresas:")
print(con.sql("select * from main.dim_cnae order by quantidade_empresas desc limit 5").df())
