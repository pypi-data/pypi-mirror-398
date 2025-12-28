import os
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.manifold import LocallyLinearEmbedding as LLE
from yellowbrick.features import PCA as yb_PCA

from .base import baseml


class DimentionReduction(baseml):  # reduction
    """BaseML中的降维模块,包含['PCA'(主成分分析), 'LDA'(线性判别分析), 'LLE'(局部线性嵌入)]降维算法.

    Attributes:
        algorithm: 算法名称
        model: 实例化的模型
    
    更多用法及算法详解可参考：https://xedu.readthedocs.io/zh/master/baseml/introduction.html
    """

    def __init__(self, algorithm='PCA', n_components=2, para={}):
        """rdc类的构造函数

        Args:
            algorithm (str, optional): 采用的降维算法. Defaults to 'PCA'.
            n_components (int, optional): 降维后保留的特征数. Defaults to 2.
            para (dict, optional): para (dict, optional): 参数字典,可自定义参数放入,参数名称详见sklearn官方文档. Defaults to {}.
        """

        super(DimentionReduction, self).__init__()   # 继承父类的构造方法
        self.algorithm = algorithm
        self.n_components = n_components

        if self.algorithm == 'PCA':     # 主成分分析
            if len(para) > 1:
                self.model = PCA(**para)
            else:
                self.model = PCA(n_components=n_components)
        elif self.algorithm == 'LDA':   # 线性判别分析
            if len(para) > 1:
                self.model = LDA(**para)
            else:
                self.model = LDA(n_components=n_components)
        elif self.algorithm == 'LLE':   # 局部线性嵌入
            if len(para) > 1:
                self.model = LLE(**para)
            else:
                self.model = LLE(n_components=n_components)

    def train(self, validate=True):
        """训练模型.

        Args:
            validate (bool, optional): 是否需要验证模型，并输出方差贡献率. Defaults to True.
        """
        if self.algorithm == 'LDA':
            if len(self.y_train) == 0:
                raise Exception("使用LDA时必须输入y标签")
            self.model.fit(self.x_train, self.y_train)
        else:
            self.model.fit(self.x_train)

        if validate and self.algorithm != 'LLE':
            explained_var = self.model.explained_variance_ratio_  # 获取贡献率
            print('累计方差贡献率为：{}'.format(explained_var))

    def inference(self, data=np.nan):
        """使用模型进行降维

        Args:
            data (numpy, optional): 放进来降维的数据,不填默认使用self.x_train.

        Returns:
            pred: 返回降维结果，保留的特征数为刚开始输进来的.
        """
        if data is not np.nan:  # 对data进行了指定
            self.x_test = data
            if self.input_shape is not None: 
                model_input_shape = str(self.input_shape).replace(str(self.input_shape[0]), 'batch')
                x_test = self.convert_np(self.x_test)   
                assert type(self.demo_input) == type(x_test), f"Error Code: -309. The data type {type(x_test)} doesn't match the model input type {type(self.demo_input)}. Example input: {self.demo_input.tolist()}."
                assert self.input_shape[1:] == x_test.shape[1:], f"Error Code: -309. The data shape {x_test.shape} doesn't match the model input shape {model_input_shape}. Example input: {self.demo_input.tolist()}."

        else:
            self.x_test = self.x_train
        self.x_test = self.convert_np(self.x_test)
        if self.x_test is not []:
            pred = self.model.transform(self.x_test)
            return pred

    def fit_transform(self):
        # 一步到位地返回降维结果
        return self.model.fit_transform(self.x_train)

    def load_dataset(self, X, y=[], type=None, x_column=[], y_column=[],
                     shuffle=True, show=False, split=False, scale=False):
        # 降维方法默认不需要split数据集
        super().load_dataset(X, y, type, x_column, y_column, shuffle, show, split, scale)

    def plot(self, X=None, y_true=None):
        """绘制降维模型图， 目前仅支持PCA.

        Args:
            X (np.ndarray, optional): 放入的测试数据, 不输入默认使用self.x_train.
            y_true (_type_, optional): 测试数据的真实标签，, 不输入默认使用self.y_train.
        """

        assert self.algorithm == 'PCA', "Error Code: -405. No implementation of this method."
        # 如果没有任何输入，默认采用x_train
        if X is None:
            if len(self.x_train) > 0:
                self.x_test = self.x_train
            assert len(
                self.x_test) > 0, "Error Code: -601. No dataset is loaded."
            X = self.x_test
            y_true = self.y_train
        X = self.convert_np(X)
        assert y_true is not None and len(y_true) > 0, \
            "Error Code: -307. The parameter {} is not set.".format("y_true")
        y_true = self.convert_np(y_true)

        self.pca_projection(X, y_true)

    def pca_projection(self, X, y_true):
        """绘制PCA投影图, 能够投影至2维或3维中, 检验数据降维的可行性

        Args:
            X (np.ndarray, optional): 放入的测试数据, 不输入默认使用self.x_train.
            y_true (_type_, optional): 测试数据的真实标签，, 不输入默认使用self.y_train.
        """
        proj = self.n_components
        proj = min(proj, 3)

        label = np.unique(y_true)
        classes = ['class_%i' % i for i in range(len(label))]
        visualizer = yb_PCA(scale=True, projection=proj, classes=classes)
        visualizer.fit_transform(X, y_true.squeeze())

        visualizer.show()
