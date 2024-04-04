from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine


# Configurações de conexão com o banco de dados
db_host = 'database-4.cg6rk0mnctnw.us-east-2.rds.amazonaws.com'
db_port = '5432' 
db_name = 'postgres'
db_user = 'postgres'
db_password = 'lepes_dados_FRM'

caminho = 'H:/Drives compartilhados/lepes_dados/equipe_dados/projeto_QPDIFGV/cadastral/'

# Leitura do arquivo Excel
cadastral = pd.read_excel(caminho + 'Copia Cadastral Itaborai.xlsx')

# Construindo a string de conexão com o banco de dados 
db_connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

# Criando uma engine de conexão com o banco de dados 
engine = create_engine(db_connection_string)

# Estabelecendo uma conexão com o banco de dados usando a engine
conn = engine.connect()

# Enviando o DataFrame para o banco de dados
cadastral.to_sql('cadastral_itaborai', con=conn, if_exists='replace', index=False)

# Fechando a conexão
conn.close()



