from typing import Annotated, Union
from uuid import UUID

from rapid_api_client.annotations import Path, PydanticBody

from remnapy.models import (
    CreateSubscriptionTemplateRequestDto,
    CreateSubscriptionTemplateResponseDto,
    DeleteSubscriptionTemplateResponseDto,
    GetTemplateResponseDto,
    GetTemplatesResponseDto,
    UpdateTemplateRequestDto,
    UpdateTemplateResponseDto,
)
from remnapy.rapid import BaseController, delete, get, patch, post


class SubscriptionsTemplateController(BaseController):
    @get("/subscription-templates", response_class=GetTemplatesResponseDto)
    async def get_all_templates(self) -> GetTemplatesResponseDto:
        """Get all subscription templates (without content)"""
        ...

    @post(
        "/subscription-templates", response_class=CreateSubscriptionTemplateResponseDto
    )
    async def create_template(
        self,
        body: Annotated[CreateSubscriptionTemplateRequestDto, PydanticBody()],
    ) -> CreateSubscriptionTemplateResponseDto:
        """Create subscription template"""
        ...

    @patch("/subscription-templates", response_class=UpdateTemplateResponseDto)
    async def update_template(
        self,
        body: Annotated[UpdateTemplateRequestDto, PydanticBody()],
    ) -> UpdateTemplateResponseDto:
        """Update subscription template"""
        ...

    @get("/subscription-templates/{uuid}", response_class=GetTemplateResponseDto)
    async def get_template_by_uuid(
        self,
        uuid: Annotated[Union[str, UUID], Path(description="Template UUID")],
    ) -> GetTemplateResponseDto:
        """Get subscription template by uuid"""
        ...

    @delete(
        "/subscription-templates/{uuid}",
        response_class=DeleteSubscriptionTemplateResponseDto,
    )
    async def delete_template(
        self,
        uuid: Annotated[Union[str, UUID], Path(description="Template UUID")],
    ) -> DeleteSubscriptionTemplateResponseDto:
        """Delete subscription template"""
        ...
