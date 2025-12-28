import time
import torch
import numpy as np
from BaseNN import nn,pth_info
import os 
import cv2

def pkl2pth(pkl_file,pth_file=None,meta={}, rnn=False, config=None):
    ckpt = torch.load(pkl_file,map_location='cpu')
    if rnn:
        if config is None:
            print("需要传入模型配置参数。")
            return 
        para = {
            'rnn':rnn,
            'config':config,
        }
    else:
        para = {
            'rnn':rnn,
        }
    info = {
        'meta':meta,
        'state_dict':ckpt,
        'para':para, 
    }
    if pth_file is None:
        filename = pkl_file.split(".")[0] + ".pth"
    else:
        filename = pth_file
    torch.save(info,filename)

def read_data(path):
    data = []
    label = []
    dir_list = os.listdir(path)

    # 将顺序读取的文件保存到该list中
    for item in dir_list:
        tpath = os.path.join(path,item)

        # print(tpath)
        for i in os.listdir(tpath):
            # print(item)
            img = cv2.imread(os.path.join(tpath,i))
            imGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # print(img)
            data.append(imGray)
            label.append(int(item))
    x = np.array(data)
    y = np.array(label)

    x = np.expand_dims(x, axis=1)
    return x, y

def mnist_demo():
    # 将老版本pkl模型转化为新版本pth模型
    classes =  {i : str(i) for i in range(10)}
    meta = {
        'tool':'BaseNN',  # 不必要
        'time': time.asctime( time.localtime(time.time()) ),  # 不必要
        'CLASSES':classes, # 必要
    }
    pkl2pth('iris_ckpt/basenn.pkl','basenn_classes.pth',meta=meta)
    # 继续训练
    model = nn()
    train_x, train_y = read_data("../../dataset/cls/mnist/training_set")
    model.load_dataset(train_x, train_y) # 载入数据
    checkpoint = 'basenn.pth'
    model.train(lr=0.1, epochs=1,batch_num=1,checkpoint=checkpoint) # 直接训练

def iris_demo():
    # 将老版本pkl模型转化为新版本pth模型
    pkl2pth('iris_ckpt/basenn.pkl','basenn.pth')
    # 继续训练
    model = nn()
    train_path = '../../dataset/iris/iris_training.csv'
    x = np.loadtxt(train_path, dtype=float, delimiter=',',skiprows=1,usecols=range(0,4)) # [120, 4]
    y = np.loadtxt(train_path, dtype=int, delimiter=',',skiprows=1,usecols=4)
    model.load_dataset(x, y)
    model.save_fold = 'checkpoints'
    checkpoint = 'basenn.pth'
    model.train(lr=0.01, epochs=10, checkpoint=checkpoint)

    if __name__=="__main__":
        # 最简用法
        pkl2pth('iris_ckpt/basenn.pkl') # 默认在同级目录下生成与pkl同名的pth文件

        # 基本用法
        pkl2pth('iris_ckpt/basenn.pkl','basenn_classes.pth') # 自行指定pth文件名称

        # 进阶用法
        meta = {
            'tool':'BaseNN',  
            'time': time.asctime( time.localtime(time.time()) ),   
        }
        pkl2pth('iris_ckpt/basenn.pkl','basenn_classes.pth',meta=meta) # 可以自行补充其他信息

        # 具体案例
        # iris_demo()
        # mnist_demo()
