import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tdsbrondata
from pyspark.sql import functions as F
from pyspark.sql.types import *

def getSecret(secretName):
    return tdsbrondata._notebookutils.credentials.getSecret(tdsbrondata.keyvaultUrl, secretName)

def getCurrentData(workspaceName, lakehouseName, schemaName, tableName, usesScd=False, scdMoment=None):
    
    abfss = f"abfss://{workspaceName}@onelake.dfs.fabric.microsoft.com/{lakehouseName}.Lakehouse/Tables/{schemaName}/{tableName}"

    data = tdsbrondata._spark.read.format("delta").load(abfss)
    
    if usesScd:
        if scdMoment is not None:
            data = data.filter(
                (F.col("ScdStartDate") <= scdMoment) &
                (
                    F.col("ScdEndDate").isNull() |
                    (F.col("ScdEndDate") > scdMoment)
                )
            )
        else:
            data = data.filter(
                (F.col("CurrentFlag") == 1) &
                (F.col("ScdEndDate").isNull())
            )

    return data

def addEventLogEntry(lakehouseName, schemaName, tableName, eventType, eventResult):

    abfss = 'abfss://Tosch-Data@onelake.dfs.fabric.microsoft.com/M_Metadata.Lakehouse/Tables/dbo'
    
    schema = StructType([
        StructField("LakehouseName", StringType(), True),
        StructField("SchemaName", StringType(), True),
        StructField("TableName", StringType(), True),
        StructField("EventType", StringType(), True),
        StructField("EventResult", StringType(), True)
    ])

    row = {"LakehouseName": lakehouseName, "SchemaName": schemaName, "TableName": tableName, "EventType": eventType, "EventResult": eventResult}
    df = tdsbrondata._spark.createDataFrame([row], schema=schema)

    try:
        dfExisting = tdsbrondata._spark.read.format("delta").load(f"{abfss}/eventlog")
    except Exception as e:
        dfExisting = tdsbrondata._spark.createDataFrame([], schema=schema)

    isDuplicate = (
        dfExisting.filter(
            (F.col("LakehouseName") == row["LakehouseName"]) &
            (F.col("SchemaName") == row["SchemaName"]) &
            (F.col("TableName") == row["TableName"]) &
            (F.col("EventType") == row["EventType"]) &
            (F.col("EventResult") == row["EventResult"])
        )
        .limit(1)
        .count() > 0
    )

    if not isDuplicate:
        df.write.mode("append").format("delta").save(f"{abfss}/eventlog")

def fileToBeProcessed(lakehouseName, schemaName, tableName, filePattern):

    shouldBeProcessed = True

    eventLog = tdsbrondata._spark.read.format("delta").load("abfss://Tosch-Data@onelake.dfs.fabric.microsoft.com/M_Metadata.Lakehouse/Tables/dbo/eventlog")

    fileAdded = eventLog.filter(
        (F.col("LakehouseName") == lakehouseName) & 
        (F.col("SchemaName") == schemaName) & 
        (F.col("TableName") == tableName) & 
        (F.col("EventType") == "fileAdded") & 
        (F.col("EventResult").startswith(filePattern))
    ).limit(1)

    fileAdded = fileAdded.collect()
    if fileAdded:
        fileName = fileAdded[0]["EventResult"]
        fileProcessed = eventLog.filter(
            (F.col("LakehouseName") == lakehouseName) & 
            (F.col("SchemaName") == schemaName) & 
            (F.col("TableName") == tableName) & 
            (F.col("EventType") == "fileProcessed") & 
            (F.col("EventResult").startswith(filePattern))
        ).limit(1)

        fileProcessed = fileProcessed.collect()
        if fileProcessed:
            shouldBeProcessed = False
    else:
        shouldBeProcessed = False

    if shouldBeProcessed:
        return fileName
    else:
        return None