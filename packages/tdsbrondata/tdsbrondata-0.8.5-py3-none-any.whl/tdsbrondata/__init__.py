from pyspark.sql.types import *

_notebookutils = None
_spark = None

schemaName = None
schemaNameBronze = None
schemaNameSilver = None
workspaceName = None
lakehouseName = None
lakehouseNameBronze = None
lakehouseNameSilver = None
keyvaultName = None
keyvaultUrl = None

sourceDataMode = None
sourceDataPeriod = None

automaticDataPath = None
manualDataPath = None
tablesRootPath = None

typeMapping = {
    "BINARY": BinaryType(),
    "BOOLEAN": BooleanType(),
    "BYTE": ByteType(),
    "DATE": DateType(),
    "DOUBLE": DoubleType(),
    "FLOAT": FloatType(),
    "INTEGER": IntegerType(),
    "LONG": LongType(),
    "STRING": StringType(),
    "TIMESTAMP": TimestampType()
}

scdColumns = [
    {"name": "SurrogateKey", "type": "LONG"},
    {"name": "CurrentFlag", "type": "BYTE"},
    {"name": "ScdStartDate", "type": "TIMESTAMP"},
    {"name": "ScdEndDate", "type": "TIMESTAMP"}
]