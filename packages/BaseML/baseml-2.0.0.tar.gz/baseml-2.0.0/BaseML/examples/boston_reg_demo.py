import sys
sys.path.append('/home/PJLAB/liangyiwen/Even/code/OpenBaseLab-Edu/')
from BaseML import Regression as reg
import numpy as np
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pandas as pd

# boston=datasets.load_boston()
# data=boston.data  # 506行，13个特征
# target=boston.target  # 506行


def boston_reg(algorithm = 'LinearRegression'): 
    model = reg(algorithm = algorithm)
    # 划分数据集

    # 指定数据集格式
    model.load_dataset(X = data, y = target, type='numpy', show=False, split=True)
    # 开始训练
    model.train(validate = True)
    # 进行推理
    result = model.inference()
    # print(result)
    # 保存模型
    model.save()

def iris_train():
    from BaseDT.dataset import split_tab_dataset
# 指定待拆分的csv数据集
    path = "Height_data.csv"
    # 指定特征数据列、标签列、训练集比重
    # tx,ty,val_x,val_y = split_tab_dataset(path,data_column=range(0,3),label_column=3,train_val_ratio=0.8)
    # 实例化模型
    model = reg(algorithm ="Polynomial")
    # 指定数据集格式
    # model.load_dataset(tx,ty,type = 'numpy')
    a = model.load_tab_data('iris_training.csv',train_val_ratio=0.8)
    # a = model.load_tab_data('Height_data.csv')
    # 开始训练
    model.train()

    model.valid('iris_training.csv',metrics='r2')
    model.metricplot()
    model.save("polynormial.pkl")

    model.load('polynormial.pkl')

def boston_reg_inference(algorithm = 'LinearRegression'): 
    # 划分数据集
    X_train, X_test, y_train, y_test=train_test_split(data,target,test_size = 0.2, random_state=42)
    # 实例化模型
    model = reg(algorithm = algorithm)
    # 加载模型权重文件
    model.load('checkpoint.pkl')
    # 进行推理
    y_pred = model.inference(X_test)
    acc = mean_squared_error(y_test, y_pred)
    print('误差为：{}'.format(acc * 100))


if __name__ == '__main__':
    # boston_reg(algorithm='Polynomial')
    # boston_reg()
    # print(reg.__doc__)
    iris_train()