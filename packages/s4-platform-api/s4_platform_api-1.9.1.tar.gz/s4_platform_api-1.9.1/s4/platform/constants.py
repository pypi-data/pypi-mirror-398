# Copyright 2023 Semaphore Solutions
# ---------------------------------------------------------------------------
import warnings


warnings.warn("Data types should be imported from s4/platform/prospective_task_config/field_type.py",
              category=DeprecationWarning)

DATA_TYPE_BOOLEAN = "http://www.w3.org/2001/XMLSchema#boolean"
DATA_TYPE_DATE = "http://www.w3.org/2001/XMLSchema#date"
DATA_TYPE_DATETIME = "http://www.w3.org/2001/XMLSchema#dateTime"
DATA_TYPE_DECIMAL = "http://www.w3.org/2001/XMLSchema#decimal"
DATA_TYPE_FILE_REFERENCE = "http://www.semaphoresolutions.com/schema/2020/platform#FileReference"
DATA_TYPE_INTEGER = "http://www.w3.org/2001/XMLSchema#integer"
DATA_TYPE_STRING = "http://www.w3.org/2001/XMLSchema#string"
DATA_TYPE_TEXT_MARKDOWN = "http://www.semaphoresolutions.com/schema/2020/platform#text/markdown"
DATA_TYPE_TYPE_REFERENCE = "http://www.semaphoresolutions.com/schema/2020/platform#TypeReference"
DATA_TYPE_URI = "http://www.w3.org/2001/XMLSchema#anyURI"

ENTITY_TYPE_CONTAINER = "http://www.semaphoresolutions.com/schema/2020/platform#Container"
ENTITY_TYPE_ENTITY = "http://www.w3.org/ns/prov#Entity"
ENTITY_TYPE_HAS_GENERIC_CONTENTS = "http://www.semaphoresolutions.com/schema/2020/platform#HasGenericContents"
ENTITY_TYPE_INSTRUMENT = "http://www.semaphoresolutions.com/schema/2020/platform#Instrument"
ENTITY_TYPE_POOL = "http://www.semaphoresolutions.com/schema/2020/platform#Pool"
ENTITY_TYPE_REAGENT = "http://www.semaphoresolutions.com/schema/2020/platform#Reagent"
ENTITY_TYPE_SAMPLE = "http://www.semaphoresolutions.com/schema/2020/platform#Sample"
