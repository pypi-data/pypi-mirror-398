from sqlalchemy import create_engine, text
from sshtunnel import SSHTunnelForwarder
try: from drilling.context_sources import *
except: from context_sources import *

class Connect():

    def __init__(self, parameters: dict):
        self.params = parameters

        # Banco
        self.db_dialect = self.params["Dialect"]
        self.db_protocol = self.params["Protocol"] + "://"
        self.db_host = self.params["Server"]
        self.db_port = self.params["Port"]
        self.db_user = self.params["User"]
        self.db_password = self.params["Pass"]
        self.db_name = self.params["Database"]
        self.db_driver = self.params["Driver"] or ""

        # SSH
        self.shh = self.params["SSH"]["Habilited"]
        self.ssh_host = self.params["SSH"].get("Host", "")
        self.ssh_port = self.params["SSH"].get("Port", 22)
        self.ssh_user = self.params["SSH"].get("User", "")
        self.ssh_password = str(self.params["SSH"].get("Pass", ""))

        # Objetos internos
        self.engine = None
        self.conn = None
        self.ssh_tunnel = None

    def __enter__(self):
        if self.shh:
            tunnel = SSHTunnelForwarder(
                (self.ssh_host, 22),
                ssh_username=self.ssh_user,
                ssh_password=self.ssh_password,
                remote_bind_address=(self.db_host, self.db_port),  # ajuste se necessário
                local_bind_address=('127.0.0.1', 0)
            )
            tunnel.start()
            self.ssh_tunnel = tunnel
            self.db_host = "127.0.0.1"
            self.db_port = self.ssh_tunnel.local_bind_port

        if self.db_dialect in ['PostgreSQL', 'SQLServer']:
            db_host = self.db_host
            db_port = self.db_port
            db_url = f"@{db_host}:{db_port}/"
            db_credentials = f"{self.db_user}:{self.db_password}"
            conn_str = f"{self.db_protocol}{db_credentials}{db_url}{self.db_name}{self.db_driver}"
            self.engine = create_engine(conn_str)
            self.conn = self.engine.connect()
            return self.conn
        

        else: raise ValueError(f"Dialect {self.db_dialect} not supported.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn: 
            self.conn.close()
        if self.engine: 
            self.engine.dispose()
        if self.ssh_tunnel:
            self.ssh_tunnel.stop()
        
if __name__ == "__main__":

    # Exemplo de uso para testes locais com sqlite em memória
    with Connect(ConPrm('Datalake_Devee')) as conn:
        result = conn.execute(text("SELECT 'success' as attempt"))
        for row in result:
            print(row)