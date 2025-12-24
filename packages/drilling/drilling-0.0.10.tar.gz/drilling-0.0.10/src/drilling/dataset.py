import pandas as pd
import yaml, calendar
from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, DateTime, Integer, Boolean, Time, Date, Numeric, inspect, insert, text
)
try: from drilling.context import *
except: from context import *

sqlalchemy_types = {
    "string": String(255),
    "text": String,
    "integer": Integer,
    "money": Numeric(19, 2),
    "datetime": DateTime,
    "boolean": Boolean,
    "time": Time,
    "date": Date,
    "float": Numeric(19, 4),
}

class Dataset:
    def __init__(self, dataframe: pd.DataFrame = pd.DataFrame(), Connect=None):
        self.connection = Connect
        self.dataframe = dataframe
        self.constrains = None
        self.schema = None
        self.table = None
        self.columns = None
        self.columns_types = None
        self.columns_names = None

        self.prm_reset_table = False
        self.prm_batch_params = None
        self.prm_batch_id = None
        self.prm_batch_number = None

        self.vlr_start_date = datetime.now()

    def set_dataframe(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe
        return self
    
    def set_assets(self, path: str):

        with open(path, "r") as file:
            data = yaml.safe_load(file)

        self.constrains = data["Constrains"]
        self.schema = data["Schema"]
        self.table = data["Table"]

        ColumnsTypes = []
        ColumnsNames = []
        for col_name, col_info in data["Columns"].items():
            ColumnsTypes.append(col_info.lower()) 
            ColumnsNames.append(col_name)

        self.columns_types = ColumnsTypes
        self.columns_names = ColumnsNames
        self.columns = dict(zip(ColumnsNames, ColumnsTypes)) 

        if self.connection.dialect.name in ['postgresql']:

            sqlalchemy_types = {
                "string": String(255),
                "text": String,
                "integer": Integer,
                "money": Numeric(19, 2),
                "datetime": DateTime,
                "boolean": Boolean,
                "time": Time,
                "date": Date,
                "float": Numeric(19, 4),
            }

            self.columns = {
                col: sqlalchemy_types[tipo]
                for col, tipo in self.columns.items()
            }
        
        return self
    
    def validate_dataset(self):

        self.dataframe = self.dataframe.reindex(columns=self.columns_names)

        for col, tipo in self.columns.items():

            if tipo == DateTime or tipo == Date:
                self.dataframe[col] = self.dataframe[col].fillna(datetime(1753, 1, 1)).astype(str).replace('1753-01-01 00:00:00', None).replace('1753-01-01', None)
            
            elif tipo == Integer:
                self.dataframe[col] = (pd.to_numeric(self.dataframe[col], errors='coerce')
                    .fillna(999999999999)
                    .astype('Int64')  # tipo inteiro com suporte a nulos
                    .astype(str)
                    .replace('999999999999', None)
                )

            else:
                self.dataframe[col] = self.dataframe[col].astype(str).replace("None", None).replace("NaT", None).replace("nan", None).replace("NaN", None)
            
        return self

    def batch(self, params: dict):
        self.prm_batch_params = params
        self.prm_batch_id = params['Id']
        self.prm_batch_number = params['SeriaNumber']
        return self
    
    def validate_database(self, ResetTable: bool = False):
        
        # Metadados para manipulação de tabelas
        metadata = MetaData(schema=self.schema)
        
        # Reflete todas as tabelas existentes no banco
        metadata.reflect(bind=self.connection)

        # Pegar somente os nomes das tabelas
        table_names = list(metadata.tables.keys())

        if f"{self.schema}.{self.table}" in table_names:
            self.prm_reset_table = ResetTable
        else:
            self.prm_reset_table = True

        # Criar a tabela dinamicamente com verificação se a coluna é uma chave primária
        if self.prm_reset_table:
            metadata.clear()
            tabela = Table(
                self.table, metadata,
                *[Column(nome, tipo, primary_key=(nome in self.constrains)) for nome, tipo in self.columns.items()],
                schema=self.schema, extend_existing=True
            )
            metadata.create_all(self.connection.engine)

    def set_batch(self, BatchMethod: str, StartDate: str, EndDate: str, ResetTable: bool = False):
        batch_type = BatchMethod
        self.validate_database(ResetTable = ResetTable)

        if self.prm_reset_table:
            StartDate = datetime(2020, 1, 1)

        start_date = StartDate.strftime('%Y-%m-%d')
        end_date = EndDate.strftime('%Y-%m-%d')
        assets = []
        nm=0
        if batch_type == "monthly":
            sy, sm, _ = map(int, start_date.split("-"))
            ey, em, _ = map(int, end_date.split("-"))

            while (sy, sm) <= (ey, em):
                batch_id = sy * 100 + sm
                batch_start = f"{sy}-{sm:02d}-01"
                batch_end = f"{sy}-{sm:02d}-{calendar.monthrange(sy, sm)[1]}"
                batch_end = batch_end

                assets.append({
                    "SeriaNumber": nm,
                    "Id": batch_id,
                    "BatchMethod": batch_type,
                    "StartDate": batch_start,
                    "EndDate": batch_end
                })
                nm += 1

                sm += 1
                if sm > 12:
                    sm = 1
                    sy += 1

        elif batch_type == "daily":
            sdate = datetime.strptime(start_date, "%Y-%m-%d")
            edate = datetime.strptime(end_date, "%Y-%m-%d")

            while sdate <= edate:
                batch_id = int(sdate.strftime("%Y%m%d"))
                batch_str = sdate.strftime("%Y-%m-%d")

                assets.append({
                    "SeriaNumber": nm,
                    "Id": batch_id,
                    "BatchMethod": batch_type,
                    "StartDate": batch_str,
                    "EndDate": batch_str
                })
                nm += 1
                sdate += timedelta(days=1)

        elif batch_type == "annual":
            sy, ey = int(start_date[:4]), int(end_date[:4])

            for year in range(sy, ey + 1):
                batch_start = f"{year}-01-01"
                batch_end = f"{year}-12-31"

                assets.append({
                    "SeriaNumber": nm,
                    "Id": year,
                    "BatchMethod": batch_type,
                    "StartDate": batch_start,
                    "EndDate": batch_end
                })
                nm += 1

        elif batch_type == "decade":
            sy, ey = int(start_date[:4]), int(end_date[:4])
            decade_start = sy - (sy % 10)

            while decade_start <= ey:
                batch_start = f"{decade_start}-01-01"
                batch_end = f"{decade_start + 9}-12-31"

                if (decade_start + 9) > ey:
                    batch_end = f"{ey}-12-31"

                batch_end = batch_end

                assets.append({
                    "SeriaNumber": nm,
                    "Id": decade_start,
                    "BatchMethod": batch_type,
                    "StartDate": batch_start,
                    "EndDate": batch_end
                })
                nm += 1
                decade_start += 10

        elif batch_type == "full":
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            batch_id = datetime.now().strftime("%Y%m%d%H%M%S")

            assets.append({
                "SeriaNumber": 0,
                "Id": f"X{batch_id}",
                "BatchMethod": batch_type,
                "StartDate": yesterday,
                "EndDate": yesterday
            })

        else:
            raise ValueError(f"batch_type inválido: {batch_type}")

        return assets
    
    def start(self):
        self.vlr_start_date = datetime.now()
        return self

    def load_dataset(self, ResetTable: bool = False):
        self.validate_dataset()
        
        values_list = self.dataframe.to_dict(orient="records")

        # Montando a query de upsert
        upsert_insert = f""" "{'", "'.join([col for col in self.columns.keys()])}" """
        upsert_update = ", ".join([f'"{col}" = EXCLUDED."{col}"' for col in self.columns.keys() if col not in self.constrains])
        upsert_keys = f""" "{'", "'.join([col for col in self.constrains])}" """
        values_placeholder = ", ".join([f":{col}" for col in self.columns.keys()])
        upsert_query = text(f"""
            INSERT INTO "{self.schema}"."{self.table}" ({upsert_insert})
            VALUES ({values_placeholder})
            ON CONFLICT ({upsert_keys}) DO UPDATE 
            SET {upsert_update};
        """)

        # Executando o upsert
        success, fails = 0,0
        for record in values_list:
            try: 
                self.connection.execute(upsert_query, record)
                success += 1
            # Logs de Erro
            except Exception as e:
                self.connection.rollback()
                fails += 1

        # Finalizando a transação
        self.connection.commit()

        # ====== Logging ======
        status_type = "SUCCESS" if fails == 0 else "PARTIAL" if success > 0 else "FAILED"
        delta = datetime.now() - self.vlr_start_date
        elapsed_exec_time = delta.total_seconds()

        log_dict = {
            "StartTime": self.vlr_start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "NameScript": FILE_NAME,
            "ClientName": CLIENT_NAME,
            "TableName": self.table,
            "TableSchema": self.schema,
            #"ProcessID": GPID,
            #"BatchStartTime": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exec_time)),
            #"LoadType": status_type,
            "BatchID": self.prm_batch_id,
            "SuccessRecords": success,
            "FailedRecords": fails,
            "TotalRecords": success + fails,
            "ElapsedTimeSec": round(elapsed_exec_time, 3),
            #"ElapsedTotalTime": round(elapsed_time, 3),
            #"PythonKernel": TYPE_PYTHON_KERNEL,
            #"BatchMethod": self._batch_params.get('BatchMethod'),
            #"BatchStartDate": self._batch_params.get('StartDate'),
            #"BatchEndDate": self._batch_params.get('EndDate'),
            #"ErrorDescription": error_desc,
            "ETLStatusDesc": status_type,
            #"BucketName": self._bucket,
            #"BucketStats": self._bucketStats
        }
        #print(log_dict)

        log_message = (
            f"| StartTime: {log_dict['StartTime']} "
            f"| Client: {log_dict['ClientName']} "
            f"| NameScript: {log_dict['NameScript']} "
            f"| BatchID: {str(log_dict['BatchID']).ljust(6)} "
            f"| Success: {str(log_dict['SuccessRecords']).rjust(5)} "
            f"| Fails: {str(log_dict['FailedRecords']).rjust(5)} "
            f"| Total: {str(log_dict['TotalRecords']).rjust(5)} "
            f"| ElapsedTime: {log_dict['ElapsedTimeSec']:.3f}s "
            f"| Status: {log_dict['ETLStatusDesc'].ljust(8)} "
        )
        print(log_message)