from typing import Annotated, Union
from uuid import UUID

from rapid_api_client import Path
from rapid_api_client.annotations import PydanticBody

from remnapy.models import (
    CreateHostRequestDto,
    CreateHostResponseDto,
    DeleteHostResponseDto,
    GetAllHostsResponseDto,
    GetAllHostTagsResponseDto,
    GetOneHostResponseDto,
    ReorderHostRequestDto,
    ReorderHostResponseDto,
    UpdateHostRequestDto,
    UpdateHostResponseDto,
)
from remnapy.rapid import BaseController, delete, get, patch, post


class HostsController(BaseController):
    @post("/hosts", response_class=CreateHostResponseDto)
    async def create_host(
        self,
        body: Annotated[CreateHostRequestDto, PydanticBody()],
    ) -> CreateHostResponseDto:
        """Create Host"""
        ...

    @patch("/hosts", response_class=UpdateHostResponseDto)
    async def update_host(
        self,
        body: Annotated[UpdateHostRequestDto, PydanticBody()],
    ) -> UpdateHostResponseDto:
        """Update Host"""
        ...

    @get("/hosts", response_class=GetAllHostsResponseDto)
    async def get_all_hosts(
        self,
    ) -> GetAllHostsResponseDto:
        """Get All Hosts"""
        ...

    @get("/hosts/tags", response_class=GetAllHostTagsResponseDto)
    async def get_hosts_tags(
        self,
    ) -> GetAllHostTagsResponseDto:
        """Get Hosts Tags"""
        ...

    @delete("/hosts/{uuid}", response_class=DeleteHostResponseDto)
    async def delete_host(
        self,
        uuid: Annotated[Union[str, UUID], Path(description="UUID of the host")],
    ) -> DeleteHostResponseDto:
        """Delete Host"""
        ...

    @get("/hosts/{uuid}", response_class=GetOneHostResponseDto)
    async def get_one_host(
        self,
        uuid: Annotated[Union[str, UUID], Path(description="UUID of the host")],
    ) -> GetOneHostResponseDto:
        """Get One Host"""
        ...

    @post("/hosts/actions/reorder", response_class=ReorderHostResponseDto)
    async def reorder_hosts(
        self,
        body: Annotated[ReorderHostRequestDto, PydanticBody()],
    ) -> ReorderHostResponseDto:
        """Reorder Hosts"""
        ...
