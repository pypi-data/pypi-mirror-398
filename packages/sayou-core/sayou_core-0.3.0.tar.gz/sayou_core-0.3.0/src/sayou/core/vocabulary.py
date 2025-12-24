class SayouClass:
    """Ontology Class Definitions (Standard Types)"""

    TOPIC = "sayou:Topic"
    TABLE = "sayou:Table"
    CODE = "sayou:Code"
    TEXT = "sayou:TextFragment"
    LIST_ITEM = "sayou:ListItem"
    DOCUMENT = "sayou:Document"
    CHUNK = "sayou:Chunk"


class SayouPredicate:
    """Relationship Definitions (Standard Edges)"""

    HAS_PARENT = "sayou:hasParent"
    NEXT = "sayou:next"
    MENTIONS = "sayou:mentions"
    BELONGS_TO = "sayou:belongsTo"


class SayouAttribute:
    """Property Keys (Standard Attributes)"""

    TEXT = "schema:text"
    SEMANTIC_TYPE = "sayou:semanticType"
    PAGE_INDEX = "sayou:pageIndex"
    PART_INDEX = "sayou:partIndex"
    SOURCE = "sayou:source"
