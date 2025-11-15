from pydantic import BaseModel


class PublishMetadata(BaseModel):
    domain: str
    overwrite: bool = False
    overwrite_rules: dict[str, bool] = {}
