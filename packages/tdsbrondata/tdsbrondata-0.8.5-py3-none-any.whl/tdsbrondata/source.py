import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tdsbrondata
from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime

def writeToParquet(df, name, loadType):
    filePath = f"{tdsbrondata.automaticDataPath}/{name}_{loadType}.parquet"

    for field in df.schema.fields:
        if field.dataType.simpleString() == "void":
            df = df.withColumn(field.name, F.col(field.name).cast(StringType()))

    for loadType in ["full", "incremental"]:
        existingFilePath = f"{tdsbrondata.automaticDataPath}/{name}_{loadType}.parquet"
        if tdsbrondata._notebookutils.fs.exists(existingFilePath):
            tdsbrondata._notebookutils.fs.rm(existingFilePath, recurse=True)

    df.write.parquet(filePath)

def writeToTable(df, name, mode):

    overwriteSchema = (mode == 'overwrite')

    tablePath = f"{tdsbrondata.tablesRootPath}/{name}"
    df.write.format("delta").mode(mode).option("overwriteSchema", overwriteSchema).save(tablePath)

def upsertTable(df, name, compositeKeyColumns):

    condition = " AND ".join([f"target.{column} = source.{column}" for column in compositeKeyColumns])

    tablePath = f"{tdsbrondata.tablesRootPath}/{name}"
    deltaTable = DeltaTable.forPath(tdsbrondata._spark, tablePath)

    deltaTable.alias("target").merge(df.alias("source"), condition).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

def getMostRecentParquetDate(name):
    sourceDataDirectory = '/'.join(tdsbrondata.automaticDataPath.rsplit('/', 1)[:-1])
    directories = tdsbrondata._notebookutils.fs.ls(sourceDataDirectory)

    dateDirectories = []
    for directory in directories:
        try:
            directoryDate = datetime.strptime(directory.name, '%Y%m%d')
            dateDirectories.append((directoryDate, directory.name))
        except ValueError:
            continue

    dateDirectories.sort(reverse=True, key=lambda x: x[0])

    if not dateDirectories:
        return None

    today = datetime.now().date()

    for date, directoryName in dateDirectories:
        if date.date() < today:
            mostRecentDirectory = f"{sourceDataDirectory}/{directoryName}"
            files = tdsbrondata._notebookutils.fs.ls(mostRecentDirectory)

            for file in files:
                if (file.name == f"{name}_full.parquet" or file.name == f"{name}_incremental.parquet"):
                    return date.strftime('%Y-%m-%d 00:00:00')

    return None
