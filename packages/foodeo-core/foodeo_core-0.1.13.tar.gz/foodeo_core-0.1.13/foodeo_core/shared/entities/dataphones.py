from pydantic import Field, BaseModel


class Dataphone(BaseModel):
    def is_valid(self, raise_exception: bool = True):
        pass

    name: str = Field(..., description="")
    key: str = Field(..., description="")
