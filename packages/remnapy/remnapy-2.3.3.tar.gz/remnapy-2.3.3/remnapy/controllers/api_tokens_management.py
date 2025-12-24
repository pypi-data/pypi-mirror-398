from typing import Annotated, Union
from uuid import UUID

from rapid_api_client import Path
from rapid_api_client.annotations import PydanticBody

from remnapy.models import (
    CreateApiTokenRequestDto,
    CreateApiTokenResponseDto,
    DeleteApiTokenResponseDto,
    FindAllApiTokensResponseDto,
)
from remnapy.rapid import BaseController, delete, get, post


class APITokensManagementController(BaseController):
    @post("/tokens", response_class=CreateApiTokenResponseDto)
    async def create(
        self,
        body: Annotated[CreateApiTokenRequestDto, PydanticBody()],
    ) -> CreateApiTokenResponseDto:
        """Create new API token"""
        ...

    @delete("/tokens/{uuid}", response_class=DeleteApiTokenResponseDto)
    async def delete(
        self,
        uuid: Annotated[Union[str, UUID], Path(description="UUID of the API token")],
    ) -> DeleteApiTokenResponseDto:
        """Delete API token"""
        ...

    @get("/tokens", response_class=FindAllApiTokensResponseDto)
    async def find_all(
        self,
    ) -> FindAllApiTokensResponseDto:
        """Get all API tokens"""
        ...
