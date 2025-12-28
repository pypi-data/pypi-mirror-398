from XEdu.hub import Workflow as wf
import numpy as np

# 模型声明
basenn = wf(task='basenn',checkpoint='basenn_iris.onnx')
# 待推理数据，此处仅以随机二维数组为例，以下为1个维度为4的特征
table = np.random.random((1, 4)).astype('float32')
# 模型推理
res = basenn.inference(data=table)
# 标准化推理结果
result = basenn.format_output(lang="zh")

# 更多用法教程详见：https://xedu.readthedocs.io/zh/master/support_resources/model_convert.html