import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tdsbrondata
from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import *
from functools import reduce

def initDeltaTable(tableName, columns, recreate):
    
    table = f"{tdsbrondata.schemaName}.{tableName}"
    tablePath = f"{tdsbrondata.tablesRootPath}/{tableName}"

    if recreate and DeltaTable.isDeltaTable(tdsbrondata._spark, tablePath):
        tdsbrondata._spark.sql(f"DROP TABLE IF EXISTS {table}")

    if not tdsbrondata._spark.catalog.tableExists(table):
        builder = DeltaTable.create(tdsbrondata._spark).tableName(tableName)

        for column in columns:
            builder = builder.addColumn(column["nameDelta"], dataType=column["type"])

        for column in tdsbrondata.scdColumns:
            builder = builder.addColumn(column["name"], dataType=column["type"])

        builder.execute()

    dt = DeltaTable.forPath(tdsbrondata._spark, tablePath)
    dt.vacuum(840)

    return dt

def applyFilters(df, filters):

    if not filters:
        return df

    conditions = reduce(
        lambda accumulator, f: accumulator & (F.col(f[0]) == f[2]) if f[1] == "==" else accumulator & (F.col(f[0]) != f[2]),
        filters,
        F.lit(True)
    )
    
    return df.filter(conditions)

def reduceExistingData(df, columns):
    
    dfCurrent = df.filter((F.col("CurrentFlag") == 1) & (F.col("ScdEndDate").isNull()))

    columnsSelected = [column["nameDelta"] for column in columns]

    return dfCurrent.select(*columnsSelected)

def reduceNewData(df, columns):
    
    columnsSelected = [column["nameSpark"] for column in columns]
    
    renameMapping = {column["nameSpark"]: column["nameDelta"] for column in columns}
    
    dfReduced = df.select(*columnsSelected)
    
    for nameOld, nameNew in renameMapping.items():
        dfReduced = dfReduced.withColumnRenamed(nameOld, nameNew)

    return dfReduced.distinct()

def getSourceData(tableName, sourceDataOptions):
    if tdsbrondata.sourceDataMode == 'automatic':
        return getAutomaticSourceData(tableName=tableName)
    elif tdsbrondata.sourceDataMode == 'manual':
        return getManualSourceData(tableName=tableName, sourceDataOptions=sourceDataOptions)

def getAutomaticSourceData(tableName):

    filePathFull = getAutomaticSourceDataPath(tableName, 'full')
    filePathIncremental = getAutomaticSourceDataPath(tableName, 'incremental')
    
    if tdsbrondata._notebookutils.fs.exists(filePathFull):
        return tdsbrondata._spark.read.parquet(filePathFull)
    elif tdsbrondata._notebookutils.fs.exists(filePathIncremental):
        return tdsbrondata._spark.read.parquet(filePathIncremental)
    else:
        raise FileNotFoundError(f"No automatic source data file found for table '{tableName}'.")

def getManualSourceData(tableName, sourceDataOptions):

    filePath = getManualSourceDataPath(tableName)
    
    if tdsbrondata._notebookutils.fs.exists(filePath):

        reader = tdsbrondata._spark.read
        
        if sourceDataOptions:
            for option, value in sourceDataOptions:
                reader = reader.option(option, value)
        
        return reader.csv(filePath)
    else:
        raise FileNotFoundError(f"No manual source data file found for table '{tableName}'.")
    
def getAutomaticSourceDataPath(tableName, loadType):
    path = f"{tdsbrondata.automaticDataPath}/{tableName}_{loadType}.parquet"
    path = path.replace(tdsbrondata.lakehouseNameSilver, tdsbrondata.lakehouseNameBronze)
    path = path.replace(tdsbrondata.schemaNameSilver, tdsbrondata.schemaNameBronze)
    return path

def getManualSourceDataPath(tableName):
    path = f"{tdsbrondata.manualDataPath}/{tdsbrondata.sourceDataPeriod}_{tableName}.csv"
    path = path.replace(tdsbrondata.lakehouseNameSilver, tdsbrondata.lakehouseNameBronze)
    path = path.replace(tdsbrondata.schemaNameSilver, tdsbrondata.schemaNameBronze)
    return path

def extractMutations(sourceData, columns, dtExisting, filters):

    dfExisting = dtExisting.toDF()
    dfExistingReduced = reduceExistingData(df=dfExisting, columns=columns)

    dfNew = applyFilters(df=sourceData, filters=filters)
    dfNewReduced = reduceNewData(df=dfNew, columns=columns)

    for columnName, dtype in dfExistingReduced.dtypes:
        dfNewReduced = dfNewReduced.withColumn(columnName, F.col(columnName).cast(dtype))

    dfMutations = dfNewReduced.exceptAll(dfExistingReduced)

    return dfMutations

def extractDeletions(sourceData, columns, primaryKey, dtExisting, filters):

    isCompositeKey = isinstance(primaryKey, list)

    dfExisting = dtExisting.toDF()
    dfExistingReduced = reduceExistingData(df=dfExisting, columns=columns)

    dfNew = applyFilters(df=sourceData, filters=filters)
    dfNewReduced = reduceNewData(df=dfNew, columns=columns)

    for columnName, dtype in dfExistingReduced.dtypes:
        dfNewReduced = dfNewReduced.withColumn(columnName, F.col(columnName).cast(dtype))

    if isCompositeKey:
        joinCondition = [dfExistingReduced[key] == dfNewReduced[key] for key in primaryKey]
    else:
        joinCondition = dfExistingReduced[primaryKey] == dfNewReduced[primaryKey]

    dfDeletions = dfExistingReduced.join(dfNewReduced, on=joinCondition, how="left_anti")

    return dfDeletions

def addSurrogateKeys(dtExisting, dfMutations):
    
    maxSurrogateKey = dtExisting.toDF().agg({"SurrogateKey": "max"}).collect()[0][0] or 0

    dfMutations = dfMutations.withColumn(
        "SurrogateKey",
        F.monotonically_increasing_id() + maxSurrogateKey + 1
    )

    return dfMutations

def updateRecords(columns, primaryKey, dtExisting, dfMutations):

    isCompositeKey = isinstance(primaryKey, list)

    if isCompositeKey:
        mergeCondition = " AND ".join([f"existing.{key} = mutations.{key}" for key in primaryKey]) + " AND existing.CurrentFlag = true"
    else:
        mergeCondition = f"existing.{primaryKey} = mutations.{primaryKey} AND existing.CurrentFlag = true"
    
    updateCondition = " OR ".join([
        f"NOT (existing.{column['nameDelta']} <=> mutations.{column['nameDelta']})"
        for column in columns
    ])

    (
        dtExisting.alias("existing")
        .merge(
            dfMutations.alias("mutations"),
            mergeCondition
        )
        .whenMatchedUpdate(
            condition=F.expr(updateCondition),
            set={
                "ScdEndDate": F.current_timestamp(),
                "CurrentFlag": F.lit(False)
            }
        )
        .execute()
    )

def insertRecords(columns, primaryKey, dtExisting, dfMutations):

    isCompositeKey = isinstance(primaryKey, list)

    if isCompositeKey:
        mergeCondition = " AND ".join([f"existing.{key} = mutations.{key}" for key in primaryKey]) + " AND existing.CurrentFlag = true"
    else:
        mergeCondition = f"existing.{primaryKey} = mutations.{primaryKey} AND existing.CurrentFlag = true"

    insertValues = {
        column["nameDelta"]: (
            F.col(f"mutations.{column['nameDelta']}")
        )
        for column in columns
    }

    insertValues.update({
        "SurrogateKey": F.col("mutations.SurrogateKey"),
        "CurrentFlag": F.lit(True),
        "ScdStartDate": F.current_timestamp(),
        "ScdEndDate": F.lit(None).cast("timestamp")
    })

    dtExisting.alias("existing") \
        .merge(
            dfMutations.alias("mutations"),
            mergeCondition
        ) \
        .whenNotMatchedInsert(
            values=insertValues
        ) \
        .execute()

def deleteRecords(primaryKey, dtExisting, dfDeletions):

    isCompositeKey = isinstance(primaryKey, list)

    if isCompositeKey:
        mergeCondition = " AND ".join([f"existing.{key} = deletions.{key}" for key in primaryKey]) + " AND existing.CurrentFlag = true"
    else:
        mergeCondition = f"existing.{primaryKey} = deletions.{primaryKey} AND existing.CurrentFlag = true"

    dtExisting.alias("existing") \
        .merge(
            dfDeletions.alias("deletions"),
            mergeCondition
        ) \
        .whenMatchedUpdate(
            set={
                "ScdEndDate": F.current_timestamp(),
                "CurrentFlag": F.lit(False)
            }
        ) \
        .execute()

def mutateDeltaTable(columns, primaryKey, dtExisting, dfMutations, dfDeletions):

    updateRecords(columns=columns, primaryKey=primaryKey, dtExisting=dtExisting, dfMutations=dfMutations)
    insertRecords(columns=columns, primaryKey=primaryKey, dtExisting=dtExisting, dfMutations=dfMutations)

    if dfDeletions is not None:
        deleteRecords(primaryKey=primaryKey, dtExisting=dtExisting, dfDeletions=dfDeletions)

def processData(tableName, columns, primaryKey, filters, recreate, sourceDataOptions=[], sourceDataOverride=None, skipDeletions=False):

    if sourceDataOverride is not None:
        sourceData = sourceDataOverride
    else:
         sourceData = getSourceData(tableName=tableName, sourceDataOptions=sourceDataOptions)

    sourceData = sourceData.toDF(*[column.replace(" ", "_") for column in sourceData.columns])
    
    dtExisting = initDeltaTable(tableName=tableName, columns=columns, recreate=recreate)

    dfMutations = extractMutations(sourceData=sourceData, columns=columns, dtExisting=dtExisting, filters=filters)
    dfMutations = addSurrogateKeys(dtExisting=dtExisting, dfMutations=dfMutations)

    if skipDeletions:
        dfDeletions = None
    else:
        dfDeletions = extractDeletions(sourceData=sourceData, columns=columns, primaryKey=primaryKey, dtExisting=dtExisting, filters=filters)

    mutateDeltaTable(columns=columns, primaryKey=primaryKey, dtExisting=dtExisting, dfMutations=dfMutations, dfDeletions=dfDeletions)