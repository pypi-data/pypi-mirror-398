from nlbone.interfaces.api.schema import BaseResponseModel


class FileOut(BaseResponseModel):
    url: str
    id: int | str = None
