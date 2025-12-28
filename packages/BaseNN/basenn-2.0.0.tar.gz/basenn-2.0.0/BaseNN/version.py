import os

__version__='0.2.0'
__path__=os.path.abspath(os.getcwd())

def parse_version_info(version_str):
    version_info = []
    for x in version_str.split('.'):
        if x.isdigit():
            version_info.append(int(x))
        elif x.find('rc') != -1:
            patch_version = x.split('rc')
            version_info.append(int(patch_version[0]))
            version_info.append(f'rc{patch_version[1]}')
    return tuple(version_info)

def hello():
                                                 
    print("""
  ____                 _   _ _   _ 
 |  _ \               | \ | | \ | |
 | |_) | __ _ ___  ___|  \| |  \| |
 |  _ < / _` / __|/ _ \ . ` | . ` |
 | |_) | (_| \__ \  __/ |\  | |\  |
 |____/ \__,_|___/\___|_| \_|_| \_|
                                      
    """)
    print("BaseNN 可以方便地逐层搭建神经网路，深入探究网络原理。")
    print("BaseNN can easily build neural networks layer by layer and deeply explore the neural network principle.")
    print("相关网址：")
    print("-文档网址 :  https://xedu.readthedocs.io")
    print("-官网网址 :  https://www.openinnolab.org.cn/pjEdu/xedu/baseedu")


version_info = parse_version_info(__version__)
# path_info = parse_version_info(__path__)
