import datetime
from typing import get_args, get_origin

from pydantic import BaseModel


class ModelUtil:
    @staticmethod
    def pydantic_type_to_sql(py_type: type[BaseModel]) -> str:
        """
        Converte tipos Pydantic para tipos SQL.
        :param py_type: Tipo Pydantic a ser convertido.
        :return: Tipo SQL correspondente.
        """
        if get_origin(py_type) is not None:
            py_type = get_args(py_type)[0]

        type_mapping = {
            int: "INTEGER",
            float: "REAL",
            str: "TEXT",
            bool: "BOOLEAN",
            list: "ARRAY",
            dict: "JSONB",
            datetime.date: "DATE",
            datetime.datetime: "TIMESTAMP",
        }
        return type_mapping.get(py_type, "TEXT")

    @staticmethod
    def generate_create_table_sql(model: type[BaseModel], table_name: str = None):
        table_name = table_name or model.__name__.lower()
        fields = []
        for field_name, field in model.model_fields.items():
            sql_type = ModelUtil.pydantic_type_to_sql(field.annotation)
            nullable = "NULL" if field.is_required() is False else "NOT NULL"
            # Adiciona PRIMARY KEY ao campo 'id'
            if field_name == "id":
                fields.append(f"    {field_name} {sql_type} {nullable} PRIMARY KEY")
            else:
                fields.append(f"    {field_name} {sql_type} {nullable}")
        fields_sql = ",\n".join(fields)
        return f"CREATE TABLE {table_name} (\n{fields_sql}\n);"
