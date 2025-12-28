import os 
import torch
import numpy as np
from torch.utils.data import Dataset
from PIL import Image
import cv2

class ImageFolderDataset(Dataset):
    def __init__(self, root, transform=None,color='RGB',batch_mode=False,scale=255.0):
        self.root = root
        self.transform = transform
        self.color = color
        self.batch_mode = batch_mode
        self.scale = scale
        self.image_paths, self.labels = self.load_image_paths_and_labels()


    def load_image_paths_and_labels(self):
        image_paths = []
        labels = []
        label_index = 0
        files = os.listdir(self.root)
        files.sort() # 排序确保文件夹按类别顺序读取
        for class_name in files:
            class_folder = os.path.join(self.root, class_name)
            if os.path.isdir(class_folder):
                for img_name in os.listdir(class_folder):
                    img_path = os.path.join(class_folder, img_name)
                    if self.batch_mode:
                        img = img_path
                    else:
                        if self.color == "grayscale":
                            # img = torch.from_numpy(np.array(Image.open(img_path))).unsqueeze(0).to(torch.float32)
                            img = torch.from_numpy(cv2.imread(img_path,cv2.IMREAD_GRAYSCALE)).unsqueeze(0).to(torch.float32) /self.scale

                        else:
                            # img = torch.from_numpy(np.array(Image.open(img_path).convert('RGB'))).permute(2,0,1).to(torch.float32)
                            img = torch.from_numpy(cv2.imread(img_path)).permute(2,0,1).to(torch.float32) /self.scale
                    image_paths.append(img)
                    labels.append(label_index)
                label_index += 1
        return image_paths, labels

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        if self.color == "grayscale":
            if self.batch_mode:
                # img = torch.from_numpy(np.array(Image.open(self.image_paths[idx]))).unsqueeze(0).to(torch.float32)
                img = torch.from_numpy(cv2.imread(self.image_paths[idx])).unsqueeze(0).to(torch.float32) /self.scale
            else:
                img = self.image_paths[idx]
        else:
            if self.batch_mode:
                # img = torch.from_numpy(np.array(Image.open(self.image_paths[idx]).convert('RGB'))).permute(2,0,1).to(torch.float32)
                img = torch.from_numpy(cv2.imread(self.image_paths[idx])).permute(2,0,1).to(torch.float32) / self.scale

            else:
                img = self.image_paths[idx]
        # print(type(img))
        if self.transform:
            img = self.transform(img)
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        # print(img.shape)
        return img, label



class TabularDataset(Dataset):
    def __init__(self, root, transform=None,color='RGB',batch_mode=False,y_type='long',task_type='cls'):
        self.task_type = task_type
        self.root = root
        self.transform = transform
        self.color = color
        self.batch_mode = batch_mode
        self.y_type = y_type
        self.x, self.y = self.load_table_and_labels()


    def load_table_and_labels(self):
        # x = np.loadtxt(self.root, dtype=float, delimiter=',',skiprows=1) # [120, 4]
        # y = np.loadtxt(self.root, dtype=int, delimiter=',',skiprows=1,usecols=4)
        data = np.loadtxt(self.root, dtype=float, delimiter=',',skiprows=1) # [120, 4]
        x = data[:,:-1]
        y = data[:, -1]
        if self.task_type == 'reg':
            y = np.expand_dims(y, axis=1)


        return x, y

    def __len__(self):
        return self.y.shape[0]

    def __getitem__(self, idx):
        x = torch.tensor(self.x[idx],dtype=torch.float)
        y = torch.tensor(self.y[idx], dtype=eval("torch.{}".format(self.y_type)))

        return x, y

class NpzDataset(Dataset):
    def __init__(self, root, batch_mode=False):
        self.root = root
        self.batch_mode = batch_mode
        self.x, self.y,self.word2idx = self.load_npz()
        # print(self.word2idx)


    def load_npz(self):
        # x = np.loadtxt(self.root, dtype=float, delimiter=',',skiprows=1) # [120, 4]
        # y = np.loadtxt(self.root, dtype=int, delimiter=',',skiprows=1,usecols=4)
        # data = np.loadtxt(self.root, dtype=float, delimiter=',',skiprows=1) # [120, 4]
        datas = np.load(self.root, allow_pickle=True)
        x = datas["data"]
        y = None
        word2idx = None
        try:
            y = datas["label"]
        except:
            pass
        try:
            word2idx = datas["word2idx"].item()
        except:
            pass
        return x, y, word2idx

    def __len__(self):
        return self.x.shape[0]

    def __getitem__(self, idx):
        x = torch.tensor(self.x[idx],dtype=torch.float)
        if self.y is not None:
            y = torch.tensor(self.y[idx], dtype=torch.float)
        else:
            y = None
        return x, y