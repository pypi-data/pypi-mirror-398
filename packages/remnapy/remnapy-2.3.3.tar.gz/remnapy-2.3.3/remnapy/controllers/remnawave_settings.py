from typing import Annotated

from rapid_api_client.annotations import PydanticBody

from remnapy.models import (
    GetRemnawaveSettingsResponseDto,
    UpdateRemnawaveSettingsRequestDto,
    UpdateRemnawaveSettingsResponseDto,
)
from remnapy.rapid import BaseController, get, patch


class RemnawaveSettingsController(BaseController):
    @get("/remnawave-settings", response_class=GetRemnawaveSettingsResponseDto)
    async def get_settings(self) -> GetRemnawaveSettingsResponseDto:
        """Get Remnawave settings"""
        ...

    @patch("/remnawave-settings", response_class=UpdateRemnawaveSettingsResponseDto)
    async def update_settings(
        self,
        body: Annotated[UpdateRemnawaveSettingsRequestDto, PydanticBody()],
    ) -> UpdateRemnawaveSettingsResponseDto:
        """Update Remnawave settings"""
        ...
