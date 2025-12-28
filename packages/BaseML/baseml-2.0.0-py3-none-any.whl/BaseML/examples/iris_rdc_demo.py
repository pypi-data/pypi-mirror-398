
from BaseML import DimentionReduction as rdc
import numpy as np
from sklearn import datasets
import pandas as pd

# 导入sklearn内置的iris数据集进行测试
X = datasets.load_iris().data
y = datasets.load_iris().target

def iris_rdc(algorithm = 'PCA'): 
    # 模型实例化
    model = rdc(algorithm=algorithm, n_components=3)
    # 指定数据集格式
    model.load_dataset(X,y,type = 'numpy')
    # 开始训练
    model.train()
    # 构建测试数据
    test_data = [[0.2,0.4,3.2,5.6],
                [2.3,1.8,0.4,2.3]]
    test_data = np.asarray(test_data)

    print(model.inference())
    result = model.inference(test_data)
    print("res:",result)

if __name__ == '__main__':
    iris_rdc('LLE')