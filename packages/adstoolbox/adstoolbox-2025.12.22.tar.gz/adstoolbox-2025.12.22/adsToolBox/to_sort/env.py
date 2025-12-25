import os
import dotenv

dotenv_file = dotenv.find_dotenv('../../.env')
dotenv.load_dotenv(dotenv_file)

pg_dwh_db = str(os.getenv('pg_dwh_db'))
pg_dwh_user = str(os.getenv('pg_dwh_user'))
pg_dwh_pwd = str(os.getenv('pg_dwh_pwd'))
pg_dwh_host = str(os.getenv('pg_dwh_host'))
pg_dwh_port = str(os.getenv('pg_dwh_port'))


mssql_dwh_db = str(os.getenv('mssql_dwh_db'))
mssql_dwh_user = str(os.getenv('mssql_dwh_user'))
mssql_dwh_pwd = str(os.getenv('mssql_dwh_pwd'))
mssql_dwh_host = str(os.getenv('mssql_dwh_host'))
mssql_dwh_port = str(os.getenv('mssql_dwh_port'))

