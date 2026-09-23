from .adapters import BelongsToOrganizationCheck
from .events import (
    OrganizationCreatedEvent,
    OrganizationDeletedEvent,
    OrganizationMemberAddedEvent,
    OrganizationMemberRemovedEvent,
    OrganizationMemberUpdatedEvent,
    OrganizationUpdatedEvent,
)
from .models import (
    OrganizationMemberModelBase,
    OrganizationModel,
    create_organization_member_model,
    create_organization_model,
    generate_slug,
)
from .organizations import Organizations
from .repositories import (
    OrganizationMemberRepository,
    OrganizationRepository,
)
from .schemas import (
    OrganizationCreateSchema,
    OrganizationMemberAddSchema,
    OrganizationMemberResponseSchema,
    OrganizationMemberUpdateSchema,
    OrganizationResponseSchema,
    OrganizationUpdateSchema,
)
from .services import (
    OrganizationMemberService,
    OrganizationService,
    OrganizationServiceRegistry,
    get_organization_member_service,
    get_organization_service,
)

__all__ = [
    "BelongsToOrganizationCheck",
    "OrganizationCreateSchema",
    "OrganizationCreatedEvent",
    "OrganizationDeletedEvent",
    "OrganizationMemberAddSchema",
    "OrganizationMemberAddedEvent",
    "OrganizationMemberModelBase",
    "OrganizationMemberRemovedEvent",
    "OrganizationMemberRepository",
    "OrganizationMemberResponseSchema",
    "OrganizationMemberService",
    "OrganizationMemberUpdateSchema",
    "OrganizationMemberUpdatedEvent",
    "OrganizationModel",
    "OrganizationRepository",
    "OrganizationResponseSchema",
    "OrganizationService",
    "OrganizationServiceRegistry",
    "OrganizationUpdateSchema",
    "OrganizationUpdatedEvent",
    "Organizations",
    "create_organization_member_model",
    "create_organization_model",
    "generate_slug",
    "get_organization_member_service",
    "get_organization_service",
]


def __getattr__(name: str):
    if name in __all__:
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
