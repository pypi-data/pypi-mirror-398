from nexo.schemas.resource import Resource, ResourceIdentifier

EXAMINATION_RESOURCE = Resource(
    identifiers=[
        ResourceIdentifier(key="examination", name="Examination", slug="examinations")
    ],
    details=None,
)


VALUE_TYPES = (bool, float, int, str)
