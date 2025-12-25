from typing import List

from pydantic import BaseModel


class UploadFileV0Response(BaseModel):
    main: str


class DeleteFilesV0Response(BaseModel):
    main: List[str]
