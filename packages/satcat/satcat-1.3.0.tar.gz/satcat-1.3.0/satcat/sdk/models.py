from datetime import datetime

try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel

json_encoders = {
    # custom output conversion for datetime
    datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
}


class Model(BaseModel):
    class Config:
        orm_mode: bool = True
        arbitrary_types_allowed: bool = True
        fields = {
            "client": {
                "exclude": ...,
            }
        }
        json_encoders = json_encoders
