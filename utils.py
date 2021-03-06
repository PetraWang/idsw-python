#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/19
# @Author  : Luke
# @File    : idsw.utils.py
# @Desc    : Utils for idsw modules, including establishing Hive connection, map dataframe dtyps to hive dtypes, etc.
import logging
import logging.config
logging.config.fileConfig('logging.ini')


def mapping_df_types(df):
    """
    Mapping table for transformation from dataframe dtype to Hive table dtype
    @param df: Pandas.DataFrame
    @return: dict
    """
    from collections import OrderedDict
    dtypeDict = OrderedDict()
    for i, j in zip(df.columns, df.dtypes):
        if "object" in str(j):
            dtypeDict.update({i: "STRING"})
        if "float" in str(j):
            dtypeDict.update({i: "FLOAT"})
        if "int" in str(j):
            dtypeDict.update({i: "BIGINT"})
        if "datetime" in str(j):
            dtypeDict.update({i: "TIMESTAMP"})
        if "bool" in str(j):
            dtypeDict.update({i: "BOOLEAN"})
    return dtypeDict


def init_spark():
    from pyspark.sql import SparkSession
    spark = SparkSession \
        .builder \
        .master("yarn") \
        .enableHiveSupport() \
        .getOrCreate()
    spark.sparkContext.setLogLevel('ERROR')
    return spark


class dataUtil:
    def __init__(self, args):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.hive_user = args["hive.username"]
        self.hive_passwd = args["hive.password"]
        self.hdfs_url = args["hdfs.url"]
        self.hdfs_user = args["hdfs.username"]

    def _get_HIVE_connection(self):
        """
        Get connection with Hive
        @return: pyhive.Connection
        """
        from pyhive import hive
        conn = hive.Connection(host='127.0.0.1', port='10000',
                               username=self.hive_user,
                               password=self.hive_passwd,
                               auth='CUSTOM', configuration={"hive.resultset.use.unique.column.names": "false"})
        return conn

    def _get_HDFS_connection(self):
        from hdfs3 import HDFileSystem
        # import subprocess
        from urllib.parse import urlsplit
        # import xml.etree.ElementTree as ET
        # url = hdfs_url
        # url = subprocess.check_output("hdfs getconf -confKey fs.defaultFS", shell=True)
        # root = ET.parse(os.getenv("HADOOP_HOME") + "/etc/hadoop/core-site.xml").getroot()
        # url = [i[1].text for i in root.iter(tag="property") if i[0].text == "fs.defaultFS"][0]
        arr = urlsplit(self.hdfs_url).netloc.split(":")
        return HDFileSystem(host=arr[0], port=int(arr[1]))# , user=self.hdfs_user)

    def PyReadParquet(self, inputUrl):
        """
        Standalone version for reading Parquet from HDFS
        @param inputUrl: String
        @return: Pandas.DataFrame
        """
        import pandas as pd
        hdfs = self._get_HDFS_connection()
        with hdfs.open(inputUrl) as reader:
            df = pd.read_parquet(reader)
        return df

    def PyWriteModel(self, model, outputUrl):
        from sklearn.externals import joblib
        hdfs = self._get_HDFS_connection()
        with hdfs.open(outputUrl, "wb") as writer:
            joblib.dump(model, writer, compress=True)

    def PyReadModel(self, inputUrl):
        from sklearn.externals import joblib
        hdfs = self._get_HDFS_connection()
        with hdfs.open(inputUrl) as reader:
            model = joblib.load(reader)
        return model

    def PyWriteParquet(self, df, outputUrl):
        """
        Standalone version for writing dataframe to Parquet file on HDFS
        @param df: Pandas.DataFrame
        @param outputUrl: String
        @return:
        """
        hdfs = self._get_HDFS_connection()
        with hdfs.open(outputUrl, "wb") as writer:
            df.to_parquet(writer)

        return

    def PyReadHive(self, inputUrl):
        """
        Standalone version for reading data from Hive
        @param inputUrl: String
        @return: Pandas.DataFrame
        """
        import pandas as pd
        conn = self._get_HIVE_connection()
        df = pd.read_sql("select * from %s" % inputUrl, conn)
        conn.close()
        return df

    def PyWriteHive(self, df, outputUrl):
        """
        Standalone version for writing dataframe to Hive
        @param df: Pandas.DataFrame
        @param outputUrl: String
        @return:
        """
        import os
        # 映射获得表结构
        dtypeDict = mapping_df_types(df)
        dtypeString = ",".join("`{}` {}".format(*i) for i in dtypeDict.items())
        # 获得Hive连接
        conn = self._get_HIVE_connection()
        cursor = conn.cursor()
        # 建表
        cursor.execute("drop table if exists %s" % outputUrl)
        cursor.execute("create table %s (%s) row format delimited fields terminated by '\t'" % (outputUrl, dtypeString))
        # 将数据写到本地临时txt文件
        df.to_csv("/tmp/" + outputUrl + ".txt", header=False, index=False, sep="\t")
        # 将本地临时txt文件内容插入表
        cursor.execute("load data local inpath '%s' overwrite into table %s" % ("/tmp/" + outputUrl + ".txt", outputUrl))
        # 删除本地临时txt文件
        os.remove("/tmp/" + outputUrl + ".txt")
        cursor.close()
        conn.close()
        self.logger.info("writen to Hive")
        return

    def PyReadCSV(self, inputUrl):
        """
        Standalone version for reading from CSV file
        @param inputUrl: String
        @return: Pandas.DataFrame
        """
        import pandas as pd
        hdfs = self._get_HDFS_connection()
        with hdfs.open(inputUrl) as reader:
            df = pd.read_csv(reader, encoding='utf-8')
        return df

    def PyWriteCSV(self, df, outputUrl):
        """
        Standalone version for writing dataframe to CSV file
        @param df: Pandas.DataFrame
        @param outputUrl: String
        @return:
        """
        hdfs = self._get_HDFS_connection()
        with hdfs.open(outputUrl) as writer:
            df.to_csv(writer, index=False, encoding='utf-8')

    @staticmethod
    def SparkReadHive(inputUrl, spark):
        """
        Spark version for reading from Hive
        @param inputUrl: String
        @param spark: SparkSession
        @return: pyspark.sql.DataFrame
        """
        return spark.sql("select * from " + inputUrl)

    @staticmethod
    def SparkWriteHive(DF, outputUrl):
        """
        Spark version for writing to Hive
        @param DF: pyspark.sql.DataFrame
        @param outputUrl: String
        @return:
        """
        DF.write.mode("overwrite").format("hive").saveAsTable(outputUrl)
        return

    @staticmethod
    def SparkReadCSV(inputUrl, spark):
        """
        Spark version for reading from CSV file
        @param inputUrl: String
        @param spark: SparkSession
        @return: pyspark.sql.DataFrame
        """
        return spark.read \
            .option("header", True).option("inferSchema", True).option("mode", "DROPMALFORMED") \
            .format("csv") \
            .load(inputUrl)

    @staticmethod
    def SparkWriteCSV(DF, outputUrl):
        DF.write.format('csv').save(outputUrl)
