import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tdsbrondata
from pyspark.sql import functions as F
from pyspark.sql.types import *

def afasDebtor(dataToCheck, lakehouseName, schemaName, tableName, afasDebtors, idColumn):

    dataToCheck = (
        dataToCheck
        .filter((F.col("CurrentFlag") == 1) & (F.col("ScdEndDate").isNull()))
        .withColumn(
            "verkooprelatie_id",
            F.trim(F.lower(F.col("verkooprelatie_id").cast("string")))
        )
        .alias("check")
    )

    afasDebtors = (
        afasDebtors
        .select("Verkooprelatie_id", "Geblokkeerd_voor_levering", "Volledig_blokkeren")
        .withColumn(
            "verkooprelatie_id",
            F.trim(F.lower(F.col("Verkooprelatie_id").cast("string")))
        )
        .alias("afas")
    )

    dienst_id = schemaName[1:].split('_')[0]

    result = (
        dataToCheck.join(afasDebtors, F.col("check.verkooprelatie_id") == F.col("afas.verkooprelatie_id"), how="left")
        .withColumn(
            "remarks",
            F.when(F.col("check.verkooprelatie_id").isNull(), "AFAS verkooprelatie leeg")
            .when(F.col("afas.verkooprelatie_id").isNull(), "AFAS verkooprelatie niet gevonden")
            .when((F.col("afas.Geblokkeerd_voor_levering") == True) | (F.col("afas.Volledig_blokkeren") == True), "AFAS verkooprelatie geblokkeerd")
        )
        .filter(F.col("remarks").isNotNull())
        .withColumn("lakehouseName", F.lit(lakehouseName))
        .withColumn("schemaName", F.lit(schemaName))
        .withColumn("tableName", F.lit(tableName))
        .withColumn("idColumn", F.lit(idColumn))
        .withColumn("id", F.col(f"check.{idColumn}"))
        .withColumn("surrogateKey", F.col("check.SurrogateKey"))
        .withColumn("dienst_id", F.lit(dienst_id))
        .select("lakehouseName", "schemaName", "tableName", "idColumn", "id", "surrogateKey", "dienst_id", F.col("check.verkooprelatie_id"), "remarks")
    )

    return result