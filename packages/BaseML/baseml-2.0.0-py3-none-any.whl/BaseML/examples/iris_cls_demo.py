
from BaseML import Classification as cls
import numpy as np
from sklearn import datasets
import pandas as pd

# 导入sklearn内置的iris数据集进行测试
X = datasets.load_iris().data
y = datasets.load_iris().target

def iris_cls(algorithm = 'MLP'): # path指定模型保存的路径
    params = {'hidden_layer_sizes':(20,40,60,20), 'activation':'logistic', 'solver':'adam'}
    # 实例化模型
    model = cls(algorithm = algorithm,params=params)
    # 指定数据集格式
    model.load_dataset(pd.DataFrame(X),pd.DataFrame(y),type = 'pandas')
    # 开始训练
    model.train()
    # 构建测试数据
    test_data = [[0.2,0.4,3.2,5.6],
                [2.3,1.8,0.4,2.3]]
    test_data = np.asarray(test_data)
    result = model.inference(test_data)
    print(result)

    model.save()

def iris_train():
    params = {'hidden_layer_sizes':(20,40,60,20), 'activation':'logistic', 'solver':'adam'}
    # 实例化模型
    model = cls(algorithm ="MLP",para=params)
    # model.para = params
    # model.set_para(hidden_layer_sizes=(20,20), activation='logistic', solver='adam')
    # model.load_dataset(pd.DataFrame(X),pd.DataFrame(y),type = 'pandas')
    a = model.load_tab_data('iris_training.csv',train_val_ratio=0.8)



    # 开始训练
    model.train(epochs=1000)

    model.metricplot()
    model.valid()

def iris_valid():
    df = pd.read_csv('iris_training.csv')
    print(df.head())
    X = df.iloc[:,:-1].values
    y = df.iloc[:,-1].values

    params = {'hidden_layer_sizes':(20,40, 20), 'activation':'logistic', 'solver':'adam'}
    # 实例化模型
    model = cls(algorithm='MLP',para=params)
    # # 指定数据集格式
    model.load_dataset(pd.DataFrame(X),pd.DataFrame(y),type = 'pandas')
    # # 开始训练
    model.train()
    # # 构建测试数据
    result = model.inference(X)
    print("result",result)
    print("y ",y)

    model.valid('iris_test.csv',metrics='accuracy')
    model.save()

def iris_test():
    params = {'hidden_layer_sizes':(20,40, 20), 'activation':'logistic', 'solver':'adam'}
    # 实例化模型
    model = cls(algorithm='MLP',para=params)
    model.load('checkpoint.pkl')

    model.inference([[6.4]])
if __name__ == '__main__':
    # iris_cls(algorithm='MLP')
    # iris_train()
    # iris_valid()
    iris_test()