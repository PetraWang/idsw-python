#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/11/19
# @Author  : Luke
# @File    : idsw.ml.multilabel.py
# @Desc    : Scripts for initializing multi-label classification models. 机器学习->模型初始化->多分类


class PyKNN:
    pass


class PyNaiveBayes:
    pass


class PyLogisticRegression:
    pass


class PyDecisionTree:
    pass


class PyRandomForest:
    def __init__(self, args):
        """
        Standalone version for initializing RandomForest multi-label classifier
        @param args: dict
        n_estimators: int
        criterion: string one of "gini" and "entropy"
        max_depth: int
        min_samples_split: int
        min_samples_leaf: int
        """
        self.outputUrl1 = args["output"][0]["value"]
        self.param = args["param"]
        self.model = None

    def getIn(self):
        return

    def execute(self):
        print("using scikit-learn")
        # 树的个数
        n_estimators = int(self.param["treeNum"])
        # 评价标准
        criterion = self.param["criterion"]
        # 最大树深度
        max_depth = int(self.param["maxDepth"])
        # 最小分割样本数
        min_samples_split = int(self.param["minSamplesSplit"])
        # 叶子节点最小样本数
        min_samples_leaf = int(self.param["minSamplesLeaf"])

        # 初始化模型
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(n_estimators=n_estimators, criterion=criterion, max_depth=max_depth,
                                            min_samples_split=min_samples_split, min_samples_leaf=min_samples_leaf)

    def setOut(self):
        from sklearn.externals import joblib
        joblib.dump(self.model, self.outputUrl1, compress=True)


class PyGBDT:
    pass


class PyMLP:
    pass


class PyAutoML:
    pass


class SparkRandomForest:
    def __init__(self, args):
        """
        Spark version for initializing RandomForest multi-label classifier
        @param args: dict
        n_estimators: int
        criterion: string one of "gini" and "entropy"
        max_depth: int
        min_samples_split: int
        min_samples_leaf: int
        """
        self.outputUrl1 = args["output"][0]["value"]
        self.param = args["param"]
        self.model = None

        print("using PySpark")
        from pyspark.sql import SparkSession

        self.spark = SparkSession \
            .builder \
            .config("spark.sql.warehouse.dir", "hdfs://10.110.18.216/user/hive/warehouse") \
            .enableHiveSupport() \
            .getOrCreate()

    def getIn(self):
        return

    def execute(self):
        from pyspark.ml.classification import RandomForestClassifier
        from pyspark.ml import Pipeline

        # 树的个数
        n_estimators = int(self.param["treeNum"])
        # 评价标准
        criterion = self.param["criterion"]
        # 最大树深度
        max_depth = int(self.param["maxDepth"])
        # 最小分割样本数
        min_samples_split = int(self.param["minSamplesSplit"])
        # 叶子节点最小样本数
        min_samples_leaf = int(self.param["minSamplesLeaf"])

        # 以Pipeline的模式初始化模型，方便统一接口加载模型
        self.model = Pipeline(stages=[
            RandomForestClassifier(numTrees=n_estimators, impurity=criterion,
                                   maxDepth=max_depth,
                                   minInstancesPerNode=min_samples_leaf)])

    def setOut(self):
        self.model.write().overwrite().save(self.outputUrl1)