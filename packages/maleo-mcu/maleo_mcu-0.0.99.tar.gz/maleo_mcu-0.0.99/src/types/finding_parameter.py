from uuid import UUID


BasicIdentifierType = int | UUID
CompositeIdentifierType = tuple[int, int]
IdentifierValueType = BasicIdentifierType | CompositeIdentifierType
