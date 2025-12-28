from nexo.schemas.resource import Resource, ResourceIdentifier

PATIENT_RESOURCE = Resource(
    identifiers=[ResourceIdentifier(key="patient", name="Patient", slug="patients")],
    details=None,
)
