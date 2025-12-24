from enum import Enum

class Feature(str, Enum):
    SIMPLE_MAPPING = "simple_mapping"
    AUTOGRAPH = "autograph"
    SEQUENCE_ARRAY = "sequence_array"
    TEMPORAL = "temporal_relationships"
    DLQ = "dead_letter_queue"
