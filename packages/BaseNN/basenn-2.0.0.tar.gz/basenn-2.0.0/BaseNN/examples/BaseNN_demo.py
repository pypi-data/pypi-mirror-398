from BaseNN import nn,pth_info
import torch
import numpy as np
import cv2
import os
from tqdm import tqdm


def load_image_data_mn():

    model = nn()
    # model.set_seed(123465)

    a = model.load_img_data("/home/user/桌面/BaseNN004/dataset/cls/mnist/training_set",
                             data_type='image_folder',color="grayscale",batch_size=20000,num_workers=0)
    model.add('Conv2D', size=(1, 6),kernel_size=( 5, 5), activation='ReLU') # 60000 * 3456(6 * 24 * 24)
    model.add('AvgPool', kernel_size=(2,2)) # 60000 * 864(6 * 12 * 12)
    model.add('Conv2D', size=(6, 16), kernel_size=(5, 5), activation='ReLU') # 60000 * 1024(16 * 8 * 8)
    model.add('AvgPool', kernel_size=(2,2)) # 60000 * 256(16 * 4 * 4)
    model.add('Linear', size=(256, 120), activation='ReLU')  # 60000 * 256
    model.add('Linear', size=(120, 84), activation='ReLU') 
    model.add('Linear', size=(84, 10), activation='Softmax')
    model.add(optimizer='SGD')
    model.save_fold = 'new_mn_ckpt'
    model.train(lr=0.01, epochs=2)#, checkpoint="new_mn_ckpt/basenn.pth") # 直接训练
    a = "../../dataset/cls/mnist/val_set/4/85.png"
    b = "../../dataset/cls/mnist/val_set/4"
    result = model.inference(data=a, checkpoint="new_mn_ckpt/basenn.pth")
    print("pth res",result)
    model.print_result()
    model.convert(checkpoint="new_mn_ckpt/basenn.pth", out_file="basenn_mn.onnx",ir_version=3)

def load_image_data_cd():
    from torchvision.transforms import transforms
    model = nn()
    model.set_seed(123465)
    tran = transforms.Resize([128,128])
    tran = {"Resize":(128,128),"RandomVerticalFlip":0.5}
    classes = {0:"cat", 1:"dog"}
    d = model.load_img_data("/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/training_set",
                             color="RGB",batch_size=1000, transform=tran,classes=classes)
    
    # for x, y in d:
    #     print(x.shape)
    model.add('Conv2D', size=(3, 6),kernel_size=( 5, 5), activation='ReLU') # 60000 * 3456(6 * 24 * 24)
    model.add('AvgPool', kernel_size=(2,2)) # 60000 * 864(6 * 12 * 12)
    model.add('Conv2D', size=(6, 16), kernel_size=(5, 5), activation='ReLU') # 60000 * 1024(16 * 8 * 8)
    model.add('AvgPool', kernel_size=(2,2)) # 60000 * 256(16 * 4 * 4)
    model.add('Linear', size=(13456, 120), activation='ReLU')  # 60000 * 256 13456
    model.add('Linear', size=(120, 10), activation='ReLU') 
    model.add('Linear', size=(10, 2), activation='Softmax')
    model.add(optimizer='Adam')
    model.save_fold = 'new_cd_ckpt'
    model.train(lr=0.001, epochs=10)# 直接训练
    # test_x, y = read_data("../../dataset/cls/mnist/val_set")
    # print(y[1000:1100])
    a = "/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/val_set/dog/dog1.jpg"
    b = "/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/val_set/cat/cat1.jpg"
    from PIL import Image
    im = Image.open(b)
    bb = np.array(im)
    result = model.inference(data=a, checkpoint="new_cd_ckpt/basenn.pth")
    print("result",result)
    model.print_result()

    model.convert(checkpoint="new_cd_ckpt/basenn.pth", out_file="basenn_cd.onnx")

def load_tab_data_iris():
    from BaseNN import nn
    import time
    model = nn()
    # 训练数据
    train_path = '../../dataset/iris/iris_training.csv'
    # x = np.loadtxt(train_path, dtype=float, delimiter=',',skiprows=1,usecols=range(0,4)) # [120, 4]
    # y = np.loadtxt(train_path, dtype=int, delimiter=',',skiprows=1,usecols=4)
    model.load_tab_data(train_path, batch_size=200000)

    model.add(layer='Linear',size=(4, 10),activation='ReLU') # [120, 10]
    model.add(layer='Linear',size=(10, 5), activation='ReLU') # [120, 5]
    model.add(layer='Linear', size=(5, 3), activation='Softmax') # [120, 3]
    model.save_fold = 'iris_ckpt'
    # a = time.time()
    model.train(lr=0.01, epochs=100)
    # print(time.time() - a)
    # print(model.device)
    # model.print_model()
    test_path = '../../dataset/iris/iris_test.csv'
    x = np.loadtxt(test_path, dtype=float, delimiter=',',skiprows=1,usecols=range(0,4)) # [120, 4]
    # y = np.loadtxt(test_path, dtype=int, delimiter=',',skiprows=1,usecols=4)
    # # print(y)
    print(x)
    res = model.inference(x,label=True, checkpoint="iris_ckpt/basenn.pth")
    print(res)
    model.convert(checkpoint="iris_ckpt/basenn.pth", out_file="basenn_iris.onnx")

def load_npz_data_action():
    # 读取数据
    X = np.load("/home/user/桌面/BaseNN004/BaseNN/examples/human_action_recognition-main/X1.npy",allow_pickle = True)
    y = np.load("/home/user/桌面/BaseNN004/BaseNN/examples/human_action_recognition-main/y1.npy", allow_pickle = True)    
    X = np.load("./conbined.npz")["data"]
    # print(X,X.shape)
    # print(X.shape)
    # np.savez("conbined.npz", data=X, label=y)
    # a = np.load("conbined.npz")
    # print(a['label'].shape)
    # train_x,train_y = X,y.astype(np.float32)
    test_x, test_y = X[28:38,:,:], y[28:38,:].astype(np.float32)
    # print(X.shape,test_x.shape, test_y.shape,test_y)
    # # 搭建模型
    model = nn()
    model.load_npz_data("./conbined.npz",batch_size=50,classes=["a", "b", "c"])
    # model.add('lstm', size=(132,128))
    # model.add('Dropout',p=0.2)
    model.add('lstm', size=(132,256))
    model.add('Dropout',p=0.2)
    # model.add('unsqueeze')
    model.add('lstm', size=(256,256))
    # model.add('squeeze')
    model.add(dim2())
    model.add('BatchNorm1d', size=256)              
    # model.add('action_model',size=(132,256))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
    model.add('linear',  size=(256, 256))
    model.add('Linear',  size=(256, 128))
    model.add('linear',  size=(128, 64))
    model.add('Linear',  size=(64, 3))
    model.add(activation='Softmax')
    model.save_fold = "action_ckpt2"
    model.train(lr=0.01, epochs=10,loss="BCELoss",metrics=[])

    res = model.inference(test_x, checkpoint="action_ckpt2/basenn.pth")
    print(test_y)
    print(res)
    model.print_result()

    model.convert(checkpoint="action_ckpt2/basenn.pth", out_file="basenn_act.onnx")

def load_npz_data_tang():
    # 读取数据
    datas = np.load('tangccc.npz',allow_pickle=True)
    data = datas['data'] 
    print("第一条数据：",data[0]) # 观察第一条数据
    word2ix = datas['word2idx'].item() # 汉字对应的索引
    # print(data.shape)
    # print(word2ix)
    # x, y = data[:,:-1], data[:, 1:]

    # np.savez("tangccc.npz", data=x, label=y, word2idx=word2ix)

    # print("词表:",word2ix) 
    # ix2word = datas['ix2word'].item() # 索引对应的汉字
    from BaseNN import nn
    model = nn()
    # model.load_dataset(x, y, word2idx=word2ix) # 载入数据
    model.load_npz_data('tangccc.npz', batch_size=128)
    # model.add('em_LSTM', size=(128,256),num_layers=2) 
    # model.save_fold = '111ckpt'
    # model.train(lr=0.005, epochs=1,checkpoint='111ckpt/basenn.pth')

    model.convert(checkpoint="111ckpt/basenn.pth", out_file="basenn_tang_12.onnx",opset_version=12)


# def cal_accuracy(y, pred_y):
#     res = pred_y.argmax(axis=1)
#     print(res, y)
#     tp = np.array(y)==np.array(res)
#     acc = np.sum(tp)/ y.shape[0]
#     return acc

# def read_data(path):
#     data = []
#     label = []
#     dir_list = os.listdir(path)

#     # 将顺序读取的文件保存到该list中
#     for item in dir_list:
#         tpath = os.path.join(path,item)

#         # print(tpath)
#         for i in os.listdir(tpath):
#             # print(item)
#             img = cv2.imread(os.path.join(tpath,i))
#             imGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#             # print(img)
#             data.append(imGray)
#             label.append(int(item))
#     x = np.array(data)
#     y = np.array(label)

#     x = np.expand_dims(x, axis=1)
#     return x, y

# def visual_feature_demo():
#     # 读取数据
#     train_x, train_y = read_data("../../dataset/cls/mnist/training_set")
#     model = nn() #声明模型 
#     model.load_dataset(train_x, train_y) # 载入数据
#     model.add('Conv2D', size=(1, 6),kernel_size=( 5, 5), activation='ReLU') # 60000 * 3456(6 * 24 * 24)
#     model.add('AvgPool', kernel_size=(2,2)) # 60000 * 864(6 * 12 * 12)
#     model.add('Conv2D', size=(6, 16), kernel_size=(5, 5), activation='ReLU') # 60000 * 1024(16 * 8 * 8)
#     model.add('AvgPool', kernel_size=(2,2)) # 60000 * 256(16 * 4 * 4)
#     model.add('Linear', size=(256, 120), activation='ReLU')  # 60000 * 256
#     model.add('Linear', size=(120, 84), activation='ReLU') 
#     model.add('Linear', size=(84, 10), activation='Softmax')
#     model.add(optimizer='SGD')
#     model.save_fold = 'mn_ckpt'
#     checkpoint = 'mn_ckpt/basenn.pth'
#     # model.train(lr=0.1, epochs=30, checkpoint=checkpoint) # 继续训练
#     # model.train(lr=0.1, epochs=1) # 直接训练

#     img = cv2.imread("/home/user/桌面/pip测试7/dataset/cls/mnist/test_set/0/0.png", cv2.IMREAD_GRAYSCALE)

#     model.visual_feature(img, in1img=True)

# def extract_feature_demo():
#     img = cv2.imread("/home/user/桌面/pip测试7/dataset/cls/mnist/test_set/0/0.png")
#     model = nn()
#     f1 = model.extract_feature(img, pretrain='resnet34')
#     print(f1.shape, f1)
#     return f1

# class LSTM_model(torch.nn.Module):
#     def __init__(self, actions):
#         super(LSTM_model, self).__init__()

#         self.actions = actions

#         self.lstm1 = torch.nn.LSTM(132, 128, batch_first=True, bidirectional=False)
#         self.dropout1 = torch.nn.Dropout(0.2)
#         self.lstm2 = torch.nn.LSTM(128, 256, batch_first=True, bidirectional=False)
#         self.dropout2 = torch.nn.Dropout(0.2)
#         self.lstm3 = torch.nn.LSTM(256, 256, batch_first=True, bidirectional=False)
#         self.bn = torch.nn.BatchNorm1d(256)
#         self.dense1 = torch.nn.Linear(256, 256)
#         self.dense2 = torch.nn.Linear(256, 128)
#         self.dense3 = torch.nn.Linear(128, 64)
#         self.dense4 = torch.nn.Linear(64, actions.shape[0])
#         self.softmax = torch.nn.Softmax(dim=1)

#     def forward(self, x):
#         x, _ = self.lstm1(x)
#         x = self.dropout1(x)
#         x, _ = self.lstm2(x)
#         x = self.dropout2(x)
#         x, _ = self.lstm3(x[:, -1, :].unsqueeze(1))
#         x = self.bn(x.squeeze())
#         x = self.dense1(x)
#         x = self.dense2(x)
#         x = self.dense3(x)
#         x = self.dense4(x)
#         x = self.softmax(x)

#         return x
# def user_defined_demo():
#     from BaseNN import nn as bnn
#     # 读取数据
#     X = np.load("/home/user/桌面/BaseNN004/BaseNN/examples/human_action_recognition-main/X1.npy",allow_pickle = True)
#     y = np.load("/home/user/桌面/BaseNN004/BaseNN/examples/human_action_recognition-main/y1.npy", allow_pickle = True)    
#     print(y.shape)
#     train_x,train_y = X,y.astype(np.float32)
#     # 自定义一个mylstm模型
#     actions = np.array(["walking","boxing","handwaving"])
#     mylstm = LSTM_model(actions)
#     # 声明模型
#     model = bnn()
#     model.load_dataset(train_x, train_y)
#     model.add(mylstm)
#     model.save_fold = "action_ud"
#     model.train(lr=0.01, epochs=200,loss="BCELoss",metrics=[])

# class MyUnsqueeze(torch.nn.Module):
#     def __init__(self, *args):
#         super(MyUnsqueeze, self).__init__()

#     def forward(self, x):
#         # print("unsqueeze",type(x), type(x[:, -1, :].unsqueeze(1)))
#         return x[:, -1, :].unsqueeze(1)
    
# class MySqueeze(torch.nn.Module):
#     def __init__(self, *args):
#         super(MySqueeze, self).__init__()

#     def forward(self, x):
#         return x.squeeze()

# class dim2(torch.nn.Module):
#     def __init__(self, *args):
#         super(dim2, self).__init__()

#     def forward(self, x):
#         return  x[:, -1, :]

# def data_define_demo():
#     # 读取数据
#     X = np.load("/home/user/桌面/BaseNN004/BaseNN/examples/human_action_recognition-main/X1.npy",allow_pickle = True)
#     y = np.load("/home/user/桌面/BaseNN004/BaseNN/examples/human_action_recognition-main/y1.npy", allow_pickle = True)    

#     train_x,train_y = X,y.astype(np.float32)
#     test_x, test_y = X[28:38,:,:], y[28:38,:].astype(np.float32)
#     # print(X.shape,train_x.shape, train_y.shape)
#     # 搭建模型
#     model = nn()
#     model.load_dataset(train_x, train_y)
#     model.add('lstm', size=(132,128))
#     model.add('Dropout',p=0.2)
#     model.add('lstm', size=(128,256))
#     model.add('Dropout',p=0.2)
#     model.add(MyUnsqueeze())
#     model.add('lstm', size=(256,256))
#     model.add(MySqueeze())
#     model.add('BatchNorm1d', size=256)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
#     model.add('Linear',  size=(256, 256))
#     model.add('Linear',  size=(256, 128))
#     model.add('linear',  size=(128, 64))
#     model.add('Linear',  size=(64, 3))
#     model.add(activation='Softmax')
#     model.save_fold = "action_ckpt1"
#     log = model.train(lr=0.01, epochs=200,loss="BCELoss",metrics=[])
#     print(log)

# def tang_infer():
#     from BaseNN import nn
#     model = nn()

#     input = '长'
#     checkpoint = '111ckpt/basenn.pth'
#     output, hidden = model.inference(data=input,checkpoint=checkpoint) # output是多维向量，接下来转化为汉字
#     print("output: ",output)
#     index = np.argmax(output) # 找到概率最大的字的索引
#     w = model.ix2word[index] # 根据索引从词表中找到字
#     print("word:",w)

# def npz2csv(npz_file,csv_file):
#     datas = np.load(npz_file,allow_pickle=True)
#     data = datas['data'] 
#     word2idx = datas['word2idx'].item() # 汉字对应的索引
#     idx2word = dict(zip(word2idx.values(),word2idx.keys()))
#     from tqdm import tqdm
#     import csv

#     with open(csv_file,'w') as f:
#         writer = csv.writer(f)
#         for line in tqdm(data):
#             verse = ""
#             for w in line:
#                 if idx2word[w] not in ['</s>','<START>']:
#                     verse += idx2word[w]
#             writer.writerow([verse])
#     # np.savetxt("tangccc.csv",np.array(content),encoding='utf-8')

# def npz2txt(npz_file,txt_file):
#     datas = np.load(npz_file,allow_pickle=True)
#     data = datas['data'] 
#     print(data.shape)
#     # print("第一条数据：",data[0]) # 观察第一条数据
#     word2idx = datas['word2ix'].item() # 汉字对应的索引
#     idx2word = dict(zip(word2idx.values(),word2idx.keys()))
#     with open(txt_file,'w',encoding='utf-8') as f:
#         for line in tqdm(data):
#             verse = ""
#             for w in line:
#                 if idx2word[w] not in ['</s>','<START>']:
#                     verse += idx2word[w]
#             f.write(verse +'\n')

# def txt2npz(txt_file,npz_file, token_size = 125):
#     with open(txt_file,'r') as f:
#         content = f.readlines()
#         content = [i.rstrip('\n') for i in content]
#         words = set() # 词表
#         for verse in content:
#             for w in verse:
#                 words.add(w)
#         word2idx = {w:i for i,w in enumerate(words)}
#         start = len(words) + 1
#         # eop = len(words) + 2
#         s = len(words) +3
#         data = []
#         for verse in tqdm(content):
#             verse_l = [start]
#             for w in verse:
#                 verse_l.append(word2idx[w])
#             # v_l.append(eop)
#             if len(verse_l) > token_size:
#                 verse_l = verse_l[:token_size]
#             else:
#                 for _ in range(token_size- len(verse_l)):
#                     verse_l.insert(0,s)
#             data.append(verse_l)
#         x, y = np.array(data)[:,:-1], np.array(data)[:, 1:]
#         print("词表大小：",len(words))
#         print("数据集大小：",x.shape[0])
#         np.savez(npz_file, data=x, label=y, word2idx=word2idx)
#         print("转化成功！保存为：",npz_file)

# def resnet_mn():
#     model = nn()
#     # model.set_seed(123465)
#     from torchvision.transforms import transforms
#     tran = transforms.Resize([224,224])
#     a = model.load_img_data("/home/user/桌面/BaseNN004/dataset/cls/mnist/training_set",
#                             batch_size=64,transform=tran,num_workers=1)
#     # model.add('Conv2D', size=(1, 6),kernel_size=( 5, 5), activation='ReLU') # 60000 * 3456(6 * 24 * 24)
#     model.add('Conv2D', size=(3, 64), kernel_size=(7, 7),stride=2,padding=3, activation='ReLU') # 60000 * 1024(16 * 8 * 8)
#     model.add('BatchNorm2d', size=64)
#     model.add('MaxPool', kernel_size=(3,3),stride=2,padding=1) # 60000 * 256(16 * 4 * 4)

#     model.add('Res_Block', size=(64, 64), num_blocks=2,stride=1)
#     model.add('Res_Block', size=(64, 128), num_blocks=2,stride=2)
#     model.add('Res_Block', size=(128, 256), num_blocks=2,stride=2)
#     model.add('Res_Block', size=(256, 512), num_blocks=2,stride=2)



#     model.add('AvgPool', kernel_size=(7,7)) # 60000 * 864(6 * 12 * 12)
#     model.add('Linear', size=(512, 10), activation='Softmax')

#     model.add(optimizer='SGD')
#     model.save_fold = 'new_mn_ckpt'
#     import time
#     a = time.time()
#     model.train(lr=0.01, epochs=1) # 直接训练
#     print(time.time() - a)
#     a = "../../dataset/cls/mnist/val_set/4/85.png"
#     b = "../../dataset/cls/mnist/val_set/4"
#     result = model.inference(data=a, checkpoint="new_mn_ckpt/basenn.pth")
#     print("pth res",result)
#     model.print_result()
#     # model.convert(checkpoint="new_mn_ckpt/basenn.pth", out_file="basenn_mn.onnx",ir_version=3)

# def diffusion_model():

#     # 导入依赖库
#     from BaseNN import nn
#     # 声明模型
#     model = nn()
#     # 载入数据
#     model.load_img_data('../../dataset/cls/MNIST-6', batch_size=64,color='grayscale',shuffle=True)
#     # # 定义模型结构：扩散模型
#     model.add('diffusion_model',img_size=28,timestep=500)
#     # 指定优化器（可省略）
#     model.add(optimizer='Adam')
#     # 正向加噪过程：原始图像->高斯噪声
#     model.color = 'grayscale'
#     # result = model.noisy("../../dataset/cls/mnist/training_set/4/2.png", timestep=500,show=True)

#     # 训练模型
#     model.save_fold = 'diffusion_ckpt500'
#     import time
#     a = time.time()
#     model.train(lr=5e-4, epochs=3,metrics=[]) # 直接训练
#     print(time.time() - a)
#     # model.train(epochs=1,metrics=[],lr=5e-4)
#     # 反向去噪过程：高斯噪声->生成图像

#     generated_imgs = model.inference(checkpoint='diffusion_ckpt500/basenn.pth',num=16, return_all_timesteps=True)
#     # print(type(generated_imgs))
#     # print(generated_imgs.shape)
#     # from matplotlib import pyplot as plt
#     # plt.imshow(np.transpose(generated_imgs[0][500],(1,2,0)))
#     # plt.show()
#     model.show(generated_imgs, size=(4,4))#,visual_timesteps=True)
#     # model.show(generated_imgs,size=(5,10),visual_timesteps=True)

def mobilenet_v2():
    # 导入依赖库
    from BaseNN import nn
    from XEdu.utils import get_similarity

    # 声明模型
    model = nn()
    # 载入数据
    
    data = model.load_img_data('/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/training_set', 
                        batch_size=700,shuffle=True,transform={'Resize':[64,64]},classes={'cat':0,'dog':1},num_workers=4)


    model.add('mobilenet_backbone')

    model.add('linear', size=(1280,1000), activation='relu')
    # model.add('dropout',p=0.2)
    # model.add('linear', size=(1000,2),activation='Softmax')
    # 指定优化器（可省略）
    model.add(optimizer='Adam')

    # 训练模型
    model.save_fold = 'mobilenet_ckpt'

    import time
    a = time.time()
    model.train(lr=1e-4, epochs=50) # 直接训练
    # model.train(lr=1e-4, epochs=30) 
    # model.train(lr=1e-4, epochs=30,metrics=['acc'],checkpoint='mobilenet_ckpt/basenn.pth') # 直接训练

    print(time.time() - a)
    # dog = model.inference( data='/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/training_set/dog/dog1.jpg')
    # model.print_result()
    # dog1 = model.inference( data='/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/training_set/dog/dog2.jpg')
    # model.print_result()
    # cat = model.inference( data='/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/training_set/cat/cat1.jpg')
    dog = model.inference(checkpoint='mobilenet_ckpt/basenn.pth',data='/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/training_set/dog/dog1.jpg')
    # model.print_result()
    print(dog)
    dog1 = model.inference(checkpoint='mobilenet_ckpt/basenn.pth',data='/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/training_set/dog/dog0.jpg')
    # model.print_result()
    print(dog1)
    cat = model.inference(checkpoint='mobilenet_ckpt/basenn.pth',data='/home/user/桌面/BaseNN004/dataset/cls/cats_dogs_dataset/CatsDogs (1)/CatsDogs/training_set/cat/cat1.jpg')
    # model.print_result()
    print(cat)
    # # 合并dog和dog1
    # dogs = np.concatenate([dog,cat],axis=0)
    
    # print(get_similarity(dog1,dogs))
    dogs = np.array([dog[0], cat[0]])
    print(get_similarity(dog1,dogs))


import torch
from torch import nn
import math


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=100):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)


class TransformerModel(nn.Module):
    def __init__(self, intoken, outtoken, hidden, nlayers=3, dropout=0.1):
        super(TransformerModel, self).__init__()
        nhead = hidden // 64

        self.encoder = nn.Embedding(intoken, hidden)
        self.pos_encoder = PositionalEncoding(hidden, dropout)

        self.decoder = nn.Embedding(outtoken, hidden)
        self.pos_decoder = PositionalEncoding(hidden, dropout)

        self.inscale = math.sqrt(intoken)
        self.outscale = math.sqrt(outtoken)

        self.transformer = nn.Transformer(d_model=hidden, nhead=nhead, num_encoder_layers=nlayers,
                                          num_decoder_layers=nlayers, dim_feedforward=hidden, dropout=dropout)
        self.fc_out = nn.Linear(hidden, outtoken)

        self.src_mask = None
        self.trg_mask = None
        self.memory_mask = None

    def generate_square_subsequent_mask(self, sz):
        mask = torch.triu(torch.ones(sz, sz), 1)
        mask = mask.masked_fill(mask == 1, float('-inf'))
        return mask

    def make_len_mask(self, inp):
        return (inp == 0).transpose(0, 1)

    def forward(self, src, trg):
        if self.trg_mask is None or self.trg_mask.size(0) != len(trg):
            self.trg_mask = self.generate_square_subsequent_mask(len(trg)).to(trg.device)

        src_pad_mask = self.make_len_mask(src)
        trg_pad_mask = self.make_len_mask(trg)

        src = self.encoder(src)
        src = self.pos_encoder(src)

        trg = self.decoder(trg)
        trg = self.pos_decoder(trg)
        output = self.transformer(src, trg, tgt_mask=self.trg_mask)
        # output = self.transformer(src, trg, src_mask=self.src_mask, tgt_mask=self.trg_mask,
        #                           memory_mask=self.memory_mask,
        #                           src_key_padding_mask=src_pad_mask, tgt_key_padding_mask=trg_pad_mask,
        #                           memory_key_padding_mask=src_pad_mask)
        output = self.fc_out(output)

        return output

from torch import LongTensor
from torch.utils.data import Dataset


class NumberLoader(Dataset):
    def __init__(self, x, y, inp_len=3, out_len=3):
        if len(x) != len(y):
            raise ValueError("len(x) != len(y)")
        self.x = [[x[i + j] for j in range(inp_len)] for i in range(len(x) - inp_len + 1)]
        self.y = [[y[i + j] for j in range(out_len)] for i in range(len(y) - out_len + 1)]

    def __getitem__(self, index):
        return LongTensor(self.x[index]), LongTensor([0] + self.y[index])

    def __len__(self):
        return len(self.x)

def train(model, criterion, optimizer, loader):
    model.train()
    epoch_loss = 0
    for i, batch in enumerate(loader):
        src, tgt = batch
        src, tgt = src.transpose(1, 0).cuda(), tgt.transpose(1, 0).cuda()
        optimizer.zero_grad()
        output = model(src, tgt[:-1, :])
        n = output.shape[-1]
        loss = criterion(output.reshape(-1, n), tgt[1:, :].reshape(-1))
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        epoch_loss += loss.item()
    return epoch_loss / len(loader)

def validation(model, criterion, loader):
    model.eval()
    epoch_loss = 0
    with torch.no_grad():
        for i, batch in enumerate(loader):
            src, tgt = batch
            src, tgt = src.transpose(1, 0).cuda(), tgt.transpose(1, 0).cuda()
            output = model(src, tgt[:-1, :])
            n = output.shape[-1]
            loss = criterion(output.reshape(-1, n), tgt[1:, :].reshape(-1))
            epoch_loss += loss.item()
    return epoch_loss / len(loader)

def tran():
    import argparse
    from numpy import arange, random
    from torch import save, load, no_grad, LongTensor
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, random_split
    # from number_loader import NumberLoader
    # from model import TransformerModel
    hidden = 128
    nlayers = 2
    voc_size = 10000
    model_name = None
    inp = arange(2, voc_size, 2)
    tgt = arange(3, voc_size, 2)
    print(tgt)
    batch_size = 8
    epochs = 30
    dataset = NumberLoader(inp, tgt)
    train_len = int(len(dataset) * 0.9)
    val_len = len(dataset) - train_len
    train_set, val_set = random_split(dataset, [train_len, val_len])
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=1)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=True, num_workers=1)
    # for i in train_loader:
    #     print(i)
    #     break
    model = TransformerModel(voc_size, voc_size, hidden=hidden, nlayers=nlayers)
    if model_name is not None:
        model.load_state_dict(load(model_name))
    model = model.cuda()
    # optimizer = optim.SGD(model.parameters(), lr=0.5)
    optimizer = optim.Adam(model.parameters())
    # scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
    criterion = nn.CrossEntropyLoss()
    best_loss = 100
    for i in range(epochs):
        epoch_loss = train(model, criterion, optimizer, train_loader)
        epoch_loss_val = validation(model, criterion, val_loader)
        # scheduler.step()
        print("epoch: {} train loss: {} val loss: {}".format(i, epoch_loss,epoch_loss_val))
        if epoch_loss_val < best_loss:
            best_loss = epoch_loss_val
            model_name = "transformer_ckpt/model_{0:.5f}.pth".format(epoch_loss_val)
            save(model.state_dict(), model_name)
    return model_name

import random
def test(max_len=3, test_times=5):
    hidden = 128
    nlayers = 2
    model = TransformerModel(10000, 10000, hidden=hidden, nlayers=nlayers)
    model.load_state_dict(torch.load("transformer_ckpt/model_1.64229.pth"))

    model = model.cuda()
    model.eval()
    with torch.no_grad():
        for i in range(test_times):
            s = random.randint(1, 4998)
            cpu_src = [(s + j) * 2 for j in range(max_len)]
            src = LongTensor(cpu_src).unsqueeze(1).cuda()
            tgt = [0] + [(s + j) * 2 + 1 for j in range(max_len)]
            pred = [0]
            for j in range(max_len):
                inp = LongTensor(pred).unsqueeze(1).cuda()
                output = model(src, inp)
                out_num = output.argmax(2)[-1].item()
                pred.append(out_num)
            print("input: ", cpu_src)
            print("target: ", tgt)
            print("predict: ", pred)


def visual_ckpt():
    from BaseNN import nn
    import time
    model = nn()
    # 训练数据
    train_path = '../../dataset/iris/iris_training.csv'
    # x = np.loadtxt(train_path, dtype=float, delimiter=',',skiprows=1,usecols=range(0,4)) # [120, 4]
    # y = np.loadtxt(train_path, dtype=int, delimiter=',',skiprows=1,usecols=4)
    model.load_tab_data(train_path, batch_size=200000)

    model.add(layer='Linear',size=(4, 10),activation='ReLU') # [120, 10]
    model.add(layer='Linear',size=(10, 5), activation='ReLU') # [120, 5]
    model.add(layer='Linear', size=(5, 3), activation='Softmax') # [120, 3]
    model.save_fold = 'iris_ckpt'
    # a = time.time()
    model.train(lr=0.01, epochs=100)
    # print(time.time() - a)
    # print(model.device)
    # model.print_model()
    # test_path = '../../dataset/iris/iris_test.csv'
    # x = np.loadtxt(test_path, dtype=float, delimiter=',',skiprows=1,usecols=range(0,4)) # [120, 4]
    # y = np.loadtxt(test_path, dtype=int, delimiter=',',skiprows=1,usecols=4)
    # # # print(y)
    # print(x)
    # res = model.inference(x,label=True, checkpoint="iris_ckpt/basenn.pth")
    # print(res)
    # model.convert(checkpoint="iris_ckpt/basenn.pth", out_file="basenn_iris.onnx")
    import torch 
    ckpt = torch.load("iris_ckpt/basenn.pth")

    for i in ckpt['state_dict'].state_dict():
        print("layer:",i,"shape:", ckpt['state_dict'].state_dict()[i].shape, "\n",ckpt['state_dict'].state_dict()[i])
        # for j in ckpt['state_dict'][i]: 

 
            # print(i,j)
        # print(i,ckpt[i])
    # print(ckpt['state_dict'][])

if __name__=="__main__":
    # load_image_data_mn()
    # load_image_data_cd()
    # load_tab_data_iris()
    # load_npz_data_action()
    load_npz_data_tang()
    # resnet_mn()
    # diffusion_model()
    # mobilenet_v2()
    # transformer()
    # tran()
    # test()
    # visual_ckpt()
