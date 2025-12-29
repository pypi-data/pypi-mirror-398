import http
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class BaseEvent(BaseModel):
    resource: str
    http_method: http.HTTPMethod = Field(alias="httpMethod")
    headers: dict
    query_parameters: Optional[dict] = Field(alias="queryStringParameters")
    path_parameters: Optional[dict] = Field(alias="pathParameters")
    body: Optional[str]

    class Config:
        populate_by_name = True

    @model_validator(mode="after")
    def validate_http_method(self):
        valid_methods = {
            http.HTTPMethod.GET,
            http.HTTPMethod.POST,
            http.HTTPMethod.PUT,
            http.HTTPMethod.DELETE,
        }
        if self.http_method not in valid_methods:
            raise ValueError(
                f"Método HTTP '{self.http_method}' não é válido. Apenas GET, POST, PUT ou DELETE são permitidos."
            )
        return self

    @model_validator(mode="after")
    def validate_body(self):
        if self.http_method in {
            http.HTTPMethod.POST,
            http.HTTPMethod.PUT,
        }:
            if not self.body:
                raise ValueError(
                    "Corpo da requisição é obrigatório para as operações POST e PUT."
                )
        return self

    @model_validator(mode="after")
    def validate_path_parameters(self):
        if self.http_method in {
            http.HTTPMethod.GET,
            http.HTTPMethod.PUT,
            http.HTTPMethod.DELETE,
        }:
            if "id" in self.resource and (
                not self.path_parameters or not self.path_parameters.get("id")
            ):
                raise ValueError(
                    "Parâmetro 'id' é obrigatório para as operações GET, PUT e DELETE."
                )
        return self
