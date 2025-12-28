import cv2
import os
import numpy as np
from skimage import feature as skif


class ImageLoader(object):
    """BaseML中的图像导入处理模块

    """
    # label2id: {'01':0}

    def __init__(self, training_set_path, testing_set_path, label2id={}, size=128):
        """ImageLoader初始化函数

        Args:
            training_set_path (str): 图片训练集路径.
            testing_set_path (str): 图片测试集路径.
            label2id (dict, optional): 自定义的标签id字典. Defaults to {}.
            size (int, optional): 图像被resize的大小,尽量不要改size,否则使用lbp或者hog可能会出错,
            但是如果原始图像过小,可以调整size . Defaults to 128.
        """
        super(ImageLoader, self).__init__()
        self.X_train = []
        self.y_train = []
        self.X_test = []
        self.y_test = []
        # ImageNet格式的数据集才能被load
        self.training_set_path = training_set_path
        self.testing_set_path = testing_set_path
        self.label2id = label2id
        self.size = size

    # 读取单张图片，进行预处理
    def pre_process(self, img_path):

        img = cv2.imread(img_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 转为灰度图
        img = cv2.resize(img, (self.size, self.size))
        img.astype(np.uint8)
        return img

    def get_label2id(self):
        # 如果为空，自己读取training_set中所有的类别，并且进行编号
        if self.label2id == {}:
            _id = 0
            for label in os.listdir(self.training_set_path):
                self.label2id[label] = _id
                _id += 1

        return self.label2id

    def get_label_by_id(self, value):
        return [k for k, v in self.label2id.items() if v == value]

    # 提取hog描述符
    def get_hog_descriptor(self, img):
        # 采用默认值设置
        window_Size = (128, 128)  # setting the window size
        block_Size = (32, 32)  # setting the block size
        block_Stride = (16, 16)  # setting the block stride
        cell_Size = (32, 32)  # setting the cell size
        no_bins = 9  # setting the number of bins
        deriv_Aperture = 1
        Sigma = -1.  # setting the value of sigma
        histogramNormType = 0
        L2HysThreshold = 0.2
        gamma = 1  # setting the value of gamma
        no_levels = 64
        signed_Gradients = True
        # running Hog descriptor
        hog = cv2.HOGDescriptor(window_Size, block_Size, block_Stride,
                                cell_Size, no_bins, deriv_Aperture, Sigma,
                                histogramNormType, L2HysThreshold, gamma, no_levels,
                                signed_Gradients)
        return hog.compute(img).T

    # 　提取lbp描述符
    def get_lbp_descriptor(self, img):

        hist_size = 256
        lbp_radius = 1
        lbp_point = 8
        # 使用LBP方法提取图像的纹理特征.
        lbp = skif.local_binary_pattern(img, lbp_point, lbp_radius, 'default')
        # 统计图像的直方图
        max_bins = int(lbp.max() + 1)
        # hist size:256
        hist, _ = np.histogram(
            lbp, normed=True, bins=max_bins, range=(0, max_bins))
        return hist

    # 获取图像特征
    def get_feature(self, img, method):  # 获取一张图片的描述子
        if method == 'hog':
            return self.get_hog_descriptor(img)
        elif method == 'lbp':
            # 返回是一维的，长度256的向量
            return self.get_lbp_descriptor(img)
        elif method == 'flatten':
            # 转成灰度图后直接展平
            return np.array(img).flatten().reshape(1, -1)

    # 构建训练集和测试集
    def get_data(self, method='hog'):

        # 如果为空，自己读取training_set中所有的类别，并且进行编号
        if self.label2id == {}:
            _id = 0
            for label in os.listdir(self.training_set_path):
                self.label2id[label] = _id
                _id += 1

        # 读取训练集中的图片，并且进行处理
        for train_label in os.listdir(self.training_set_path):
            for image in os.listdir(os.path.join(self.training_set_path, train_label)):
                image_url = os.path.join(
                    self.training_set_path, train_label, image)
                img_processed = self.pre_process(image_url)
                img_feature = self.get_feature(img_processed, method)
                self.X_train.append(img_feature)  # 转置后是一行的
                self.y_train.append(self.label2id[train_label])

        # 读取测试集中的图片，进行处理
        for test_label in os.listdir(self.testing_set_path):
            for image in os.listdir(os.path.join(self.testing_set_path, test_label)):
                image_url = os.path.join(
                    self.testing_set_path, test_label, image)
                img_processed = self.pre_process(image_url)
                img_feature = self.get_feature(img_processed, method)
                self.X_test.append(img_feature)
                self.y_test.append(self.label2id[test_label])

        # Convert train and test data to numpy arrays
        self.X_train = np.array(self.X_train)
        self.X_train = self.X_train.reshape(
            (self.X_train.shape[0], -1))  # 转成二维数组
        self.y_train = np.array(self.y_train)
        self.X_test = np.array(self.X_test)
        self.X_test = self.X_test.reshape((self.X_test.shape[0], -1))  # 转成二维数组
        self.y_test = np.array(self.y_test)

        return self.X_train, self.y_train, self.X_test, self.y_test
