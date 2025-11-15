from pydantic import BaseModel


class PublishMetadata(BaseModel):
    domain: str
    overwrite: bool = False
    overwrite_rules: dict[str, bool] = {}
    
    async def pre_publish(self):
        pass
    
    async def post_publish(self):
        pass