from nexo.schemas.resource import Resource, ResourceIdentifier
from ..enums.checkup import Process, CheckupStatus

CHECKUP_RESOURCE = Resource(
    identifiers=[ResourceIdentifier(key="checkup", name="Checkup", slug="checkups")],
    details=None,
)


STATUS_TRANSITION_MAP: dict[CheckupStatus, CheckupStatus] = {
    CheckupStatus.DRAFT: CheckupStatus.ONGOING,
    CheckupStatus.ONGOING: CheckupStatus.REVIEWED,
    CheckupStatus.REVIEWED: CheckupStatus.APPROVED,
}


PROCESS_STATUS_MAP: dict[Process, CheckupStatus] = {
    Process.START: CheckupStatus.ONGOING,
    Process.REVIEW: CheckupStatus.REVIEWED,
    Process.APPROVE: CheckupStatus.APPROVED,
}
