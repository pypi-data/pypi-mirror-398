"""Настройки для подключения к S3."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'S3Settings',
]


class S3Settings(BaseSettings):
    """Конфигурация подключения к S3.

    Args:
        bucket: Имя S3-бакета.
        access_key: Ключ доступа AWS/S3.
        secret_key: Секретный ключ AWS/S3.
        region: Регион S3.
        endpoint_url: URL эндпоинта S3 (например, для MinIO).
        path_style: Включает использование path-style addressing.
            Если True, запросы будут формироваться в виде
            ``https://endpoint/bucket/key`` (необходимо для MinIO и
            совместимых сервисов). Если False — используется
            virtual-hosted style ``https://bucket.endpoint/key`` (дефолт AWS).
        signature_version: Версия алгоритма подписи запросов к S3.
        max_attempts: Максимальное число повторных попыток.
        connect_timeout: Таймаут подключения в секундах.
        read_timeout: Таймаут чтения в секундах.
    """

    model_config = SettingsConfigDict(
        env_prefix='S3_',
        extra='ignore',
    )

    bucket: str = Field(alias='s3_bucket')
    access_key: str = Field(alias='s3_access_key')
    secret_key: str = Field(alias='s3_secret_key')
    region: str = Field(alias='s3_region')
    endpoint_url: str = Field(alias='s3_endpoint_url')
    path_style: bool = True
    signature_version: str = 's3v4'
    max_attempts: int = 3
    connect_timeout: int = 5
    read_timeout: int = 30
