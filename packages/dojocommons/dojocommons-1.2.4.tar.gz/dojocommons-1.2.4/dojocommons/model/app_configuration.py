from typing import Optional

from pydantic_settings import BaseSettings


class AppConfiguration(BaseSettings):
    app_name: str
    app_version: str
    s3_bucket: str
    s3_path: str
    aws_region: str = "sa-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_endpoint: Optional[str] = None

    @property
    def s3_file_path(self) -> str:
        return f"s3://{self.s3_bucket}/{self.s3_path}"

    class Config:
        env_file = ".env"
