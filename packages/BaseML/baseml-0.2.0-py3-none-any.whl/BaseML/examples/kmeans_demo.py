
from BaseML import Cluster
import numpy as np

N_CLUSTERS = 7                                     # 类簇的数量
DATA_PATH = 'China_cities.csv'              # 数据集路径


def kmeans_train(num_cluster,model_path):
    # 实例化模型
    model = Cluster(algorithm = 'Kmeans', N_CLUSTERS=num_cluster)
    # 指定数据集的路径
    model.load_dataset(DATA_PATH, type='csv', x_column=[2,3], y_column=[0],split=False)

    # 开始训练
    model.train()
    # 模型保存
    model.save(model_path)

def kmeans_inference(num_cluster,model_path):
    # 实例化模型
    model = Cluster(algorithm = 'Kmeans', N_CLUSTERS=num_cluster)
    # 加载模型数据集
    model.load_dataset(DATA_PATH, type='csv', x_column=[2,3], y_column=[0], show=False, split=False)
    # 加载模型权重文件
    model.load(model_path)
    # 进行推理
    model.inference()

def gdp():
    # 实例化模型
    model = Cluster(algorithm = 'Kmeans', N_CLUSTERS=N_CLUSTERS)
    # 指定数据集的路径
    model.load_dataset("2016地区GDP.csv", type='csv', x_column=[1,2])


    # 开始训练
    model.train(validate=True)
    # model.valid(metrics='silhouette_score')
    model.valid(metrics='calinski_harabasz_score')
    # model.valid(metrics='davies_bouldin_score')
    # 模型保存
    model.save('gdp_checkpoint.pkl')


if __name__ == '__main__':
    # city()
    gdp()
    # kmeans_train(5,'checkpoint.pkl')
    # kmeans_inference(5,'checkpoint.pkl')

