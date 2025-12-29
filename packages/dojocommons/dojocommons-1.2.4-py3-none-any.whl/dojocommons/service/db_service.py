import os

import duckdb
from pydantic import BaseModel

from dojocommons.model.app_configuration import AppConfiguration
from dojocommons.util.model_util import ModelUtil


class DbService:
    def __init__(self, app_cfg: AppConfiguration):
        self._app_cfg = app_cfg
        self._conn = duckdb.connect()
        self._init_duckdb()
        print(f"[DEBUG][DbService] bucket: {self._app_cfg.s3_bucket}, path: {self._app_cfg.s3_path}")

    def __del__(self):
        self.close_connection()

    def _init_duckdb(self):
        print(f"[DEBUG][DbService] bucket: {self._app_cfg.s3_bucket}, path: {self._app_cfg.s3_path}")
        print(f"[DEBUG][DbService] aws_endpoint: {self._app_cfg.aws_endpoint}")

        self._conn.execute("SET home_directory='/tmp'")
        self._conn.execute("INSTALL httpfs; LOAD httpfs;")
        # Configura credenciais AWS
        self._conn.execute("SET s3_access_key_id='test';")
        self._conn.execute("SET s3_secret_access_key='test';")
        self._conn.execute("SET s3_region='us-east-1';")

        print(f"[DEBUG][DbService] Credenciais AWS configuradas")
        if self._app_cfg.aws_endpoint is not None:
            print(f"[DEBUG][DbService] Configurando endpoint: {self._app_cfg.aws_endpoint}")
            self._conn.execute(
                "SET s3_access_key_id=?;", (self._app_cfg.aws_access_key_id,)
            )
            print(f"[DEBUG][DbService] s3_access_key_id: {self._app_cfg.aws_access_key_id}")
            self._conn.execute(
                "SET s3_secret_access_key=?;", (self._app_cfg.aws_secret_access_key,)
            )
            print(f"[DEBUG][DbService] s3_secret_access_key: {self._app_cfg.aws_secret_access_key}")
            self._conn.execute(
                "SET s3_region=?;", (self._app_cfg.aws_region,)
            )
            self._conn.execute("SET s3_url_style='path';")
            self._conn.execute("SET s3_use_ssl=false;")
            home_dir = os.environ.get("HOME", "/tmp")
            if not os.path.exists(home_dir):
                os.makedirs(home_dir)
            #self._conn.execute(f"SET home_directory='{home_dir}'")
            self._conn.execute("SET s3_endpoint=?;", (self._app_cfg.aws_endpoint,))
        
        # Testa a configuração
        try:
            result = self._conn.execute("SELECT current_setting('s3_endpoint');").fetchone()
            print(f"[DEBUG][DbService] s3_endpoint atual: {result}")
        except Exception as e:
            print(f"[DEBUG][DbService] Erro ao verificar endpoint: {e}")

    def create_table(self, class_type: type[BaseModel], table_name: str | None = None):
        """
        Cria uma tabela DuckDB a partir de um modelo Pydantic.
        :param class_type: Modelo Pydantic que define a estrutura da tabela.
        :param table_name: Nome da tabela a ser criada. Se não fornecido, usa o nome da classe.
        :return: Resultado da execução da consulta.
        """
        if table_name is None:
            table_name = class_type.__name__.lower()

        try:
            self.create_table_from_parquet(table_name)
        except duckdb.IOException:
            self.create_table_from_model(class_type)

    def create_table_from_model(self, class_type: type[BaseModel]):
        """
        Cria uma tabela DuckDB a partir de um modelo Pydantic.
        :param class_type: Modelo Pydantic que define a estrutura da tabela.
        :return: Resultado da execução da consulta.
        """
        query = ModelUtil.generate_create_table_sql(class_type)
        self.execute_query(query)

    def create_table_from_parquet(self, table_name: str):
        """
        Cria uma tabela no DuckDB a partir de um arquivo Parquet armazenado
            no S3.
        :param table_name: Nome da tabela a ser criada.
        :return: Resultado da execução da consulta.
        """
        file_path = f"{self._app_cfg.s3_file_path}/{table_name}.parquet"
        query = (
            f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * "
            f"FROM read_parquet('{file_path}');"
        )
        self.execute_query(query)

    def persist_data(self, table_name: str):
        """
        Persiste dados de uma tabela DuckDB para um arquivo Parquet no S3.
        :param table_name: Nome da tabela a ser persistida.
        :return: Resultado da execução da consulta.
        """
        file_path = f"{self._app_cfg.s3_file_path}/{table_name}.parquet"
        query = f"COPY {table_name} TO '{file_path}'"
        print(f"[DEBUG][DbService] Parquet path: {file_path} and query: {query}")
        query += " (FORMAT PARQUET, COMPRESSION ZSTD)"
        return self.execute_query(query)

    def execute_query(self, query: str, params: tuple = None):
        """
        Executa uma consulta na conexão DuckDB.
        :param query: Consulta SQL a ser executada.
        :param params: Parâmetros para uma instrução preparada.
        :return: Resultado da execução da consulta.
        """
        if params is None:
            return self._conn.execute(query)
        return self._conn.execute(query, params)

    def close_connection(self):
        """
        Fecha a conexão com o DuckDB.
        """
        self._conn.close()
