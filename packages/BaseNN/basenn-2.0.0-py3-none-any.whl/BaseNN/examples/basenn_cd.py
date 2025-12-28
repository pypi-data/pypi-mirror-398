from XEdu.hub import Workflow as wf
import numpy as np

# 模型声明
basenn = wf(task='basenn',checkpoint='basenn_cd.onnx')
# 待推理图像，此处仅以随机数组为例，以下为1张3通道的128*128的图像。
image = np.random.random((1, 3, 128, 128)).astype('float32') # 可替换成您想要推理的图像路径,如 image = 'cat.jpg'
# 模型推理
res = basenn.inference(data=image)
# 标准化推理结果
result = basenn.format_output(lang="zh")

# 更多用法教程详见：https://xedu.readthedocs.io/zh/master/support_resources/model_convert.html