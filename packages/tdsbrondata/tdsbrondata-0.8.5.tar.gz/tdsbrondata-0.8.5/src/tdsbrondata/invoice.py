import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tdsbrondata
from pyspark.sql import functions as F
from pyspark.sql.types import *
from delta.tables import DeltaTable
from functools import reduce

itemsRequiredColumns = {
    "DienstId": IntegerType(),
    "Source": StringType(),
    "SurrogateKey": LongType(),
    "FacturatieMaand": StringType(),
    "VerkooprelatieId": StringType(),
    "ItemCode": StringType(),
    "Aantal": FloatType()
}

itemsOptionalColumns = {
    "AfwijkendePrijs": FloatType(),
    "DatumVanOrigineel": StringType(),
    "DatumTotOrigineel": StringType(),
    "AantalOrigineel": FloatType(),
    "DurationOrigineel": FloatType(),
    "EntityType": StringType(),
    "EntityId": StringType()
}

def validateItemsSchema(items):
    schemaDict = {f.name: f.dataType for f in items.schema.fields}

    for columnName, expectedType in itemsRequiredColumns.items():
        if columnName not in schemaDict:
            raise ValueError(f"Missing required column '{columnName}'")
        if type(schemaDict[columnName]) != type(expectedType):
            raise TypeError(f"Column '{columnName}' has type {schemaDict[columnName]}, expected {expectedType}")

    for columnName, expectedType in itemsOptionalColumns.items():
        if columnName in schemaDict and type(schemaDict[columnName]) != type(expectedType):
            raise TypeError(f"Column '{columnName}' has type {schemaDict[columnName]}, expected {expectedType}")

def writeItems(items):

    # TEMP: Later voor waarschuwen
    items = items.filter(F.col("VerkooprelatieId").isNotNull())
    items = items.filter(F.col("ItemCode").isNotNull())

    items = items.withColumn("ItemId", F.expr("uuid()"))
    items = writeLines(items)

    table = "items"
    tablePath = f"{tdsbrondata.tablesRootPath}/{table}"

    if DeltaTable.isDeltaTable(tdsbrondata._spark, tablePath):
        deltaTable = DeltaTable.forPath(tdsbrondata._spark, tablePath)
        facturatieMaand = items.select("FacturatieMaand").head()["FacturatieMaand"]
        deltaTable.delete(f"FacturatieMaand = '{facturatieMaand}'")
        items.write.format("delta").mode("append").save(tablePath)
    else:
        items.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(tablePath)

def writeLines(items):

    table = "lines"
    tablePath = f"{tdsbrondata.tablesRootPath}/{table}"
    facturatieMaand = items.select("FacturatieMaand").head()["FacturatieMaand"]

    # Split into items to preserve and to items aggregate

    existingItemsOptionalColumns = [col for col in itemsOptionalColumns.keys() if col in items.columns]

    if existingItemsOptionalColumns:
        filterExpression = " AND ".join([f"{col} IS NULL" for col in existingItemsOptionalColumns])
        itemsToPreserve = items.filter(f"NOT ({filterExpression})")
        itemsToAggregate = items.filter(filterExpression)
    else:
        itemsToPreserve = items.limit(0)
        itemsToAggregate = items

    for col, colType in itemsOptionalColumns.items():
        if col not in items.columns:
            itemsToAggregate = itemsToAggregate.withColumn(col, F.lit(None).cast(colType))
            itemsToPreserve = itemsToPreserve.withColumn(col, F.lit(None).cast(colType))

    # Make lines for items to preserve

    itemsToPreserve = itemsToPreserve.withColumn("LineId", F.expr("uuid()")).cache()
    linesFromItemsToPreserve = itemsToPreserve.drop("ItemId")
    linesFromItemsToPreserve = linesFromItemsToPreserve.withColumn(
        "HasItems",
        F.when(F.col("SurrogateKey").isNotNull(), True).otherwise(False)
    ).drop("Source", "SurrogateKey", "EntityType", "EntityId")

    # Make lines for items to aggregate

    linesFromItemsToAggregate = (
        itemsToAggregate
        .groupBy("DienstId", "FacturatieMaand", "VerkooprelatieId", "ItemCode")
        .agg(
            F.sum("Aantal").alias("Aantal"),
            F.collect_list("SurrogateKey").alias("SurrogateKeys")
        )
        .withColumn("LineId", F.expr("uuid()"))
    )

    for col, colType in itemsOptionalColumns.items():
        if col not in linesFromItemsToAggregate.columns:
            linesFromItemsToAggregate = linesFromItemsToAggregate.withColumn(col, F.lit(None).cast(colType))

    linesFromItemsToAggregate = linesFromItemsToAggregate.withColumn(
        "HasItems",
        F.expr("size(SurrogateKeys) > 0")
    ).drop("Source", "SurrogateKey", "EntityType", "EntityId")

    # Separate lines with and without items

    linesWithItems = linesFromItemsToAggregate.filter(F.col("HasItems") == True)
    linesWithoutItems = linesFromItemsToAggregate.filter(F.col("HasItems") == False)

    # Attach items to lines that have items

    if linesWithItems.count() > 0:
        itemsAttachedToLines = (
            linesWithItems
            .select(
                "LineId",
                F.explode("SurrogateKeys").alias("SurrogateKey"),
                "DienstId",
                "FacturatieMaand",
                "VerkooprelatieId",
                "ItemCode"
            )
            .join(
                itemsToAggregate,
                on=[
                    "SurrogateKey",
                    "DienstId",
                    "FacturatieMaand",
                    "VerkooprelatieId",
                    "ItemCode"
                ],
                how="left"
            )
        )
    else:
        itemsAttachedToLines = tdsbrondata._spark.createDataFrame([], schema=itemsToAggregate.schema)
        itemsAttachedToLines = itemsAttachedToLines.withColumn("LineId", F.lit(None).cast(StringType()))

    # Identify items not attached to any line

    attachedItemIds = itemsAttachedToLines.select("ItemId").distinct()
    itemsNotAttachedToLines = itemsToAggregate.join(attachedItemIds, on="ItemId", how="left_anti")
    itemsNotAttachedToLines = itemsNotAttachedToLines.withColumn("LineId", F.lit(None).cast(StringType()))

    # Combine

    itemsToAggregate = itemsAttachedToLines.unionByName(itemsNotAttachedToLines)
    linesFromItemsToAggregate = linesFromItemsToAggregate.drop("SurrogateKeys")

    # Final

    items = itemsToPreserve.unionByName(itemsToAggregate)
    items = items.withColumnRenamed("ItemId", "Id")

    lines = linesFromItemsToPreserve.unionByName(linesFromItemsToAggregate)
    lines = lines.withColumnRenamed("LineId", "Id")

    if DeltaTable.isDeltaTable(tdsbrondata._spark, tablePath):
        deltaTable = DeltaTable.forPath(tdsbrondata._spark, tablePath)
        deltaTable.delete(f"FacturatieMaand = '{facturatieMaand}'")
        lines.write.format("delta").mode("append").save(tablePath)
    else:
        lines.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(tablePath)

    return items

def mergeItems(lists, facMonth):

    items = []

    schemas = [row.NotebookName for row in lists.select("NotebookName").distinct().collect()]
    for schema in schemas:
        
        df = tdsbrondata.utils.getCurrentData(
            workspaceName='Tosch-Facturatie',
            lakehouseName='B_Datawarehouse',
            schemaName=schema,
            tableName='items',
            usesScd=False
        )

        df = df.filter(F.col("FacturatieMaand") == facMonth)
        
        items.append(df)

    dfItems = reduce(lambda df1, df2: df1.unionByName(df2), items)

    return dfItems

def mergeLines(lists, facMonth):

    lines = []

    schemas = [row.NotebookName for row in lists.select("NotebookName").distinct().collect()]
    for schema in schemas:
        df = tdsbrondata.utils.getCurrentData(
            workspaceName='Tosch-Facturatie',
            lakehouseName='B_Datawarehouse',
            schemaName=schema,
            tableName='lines',
            usesScd=False
        )

        df = df.filter(F.col("FacturatieMaand") == facMonth)
        
        lines.append(df)

    dfLines = reduce(lambda df1, df2: df1.unionByName(df2), lines)

    return dfLines

