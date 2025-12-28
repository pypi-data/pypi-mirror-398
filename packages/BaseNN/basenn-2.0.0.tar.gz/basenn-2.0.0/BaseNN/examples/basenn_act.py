from XEdu.hub import Workflow as wf
import numpy as np

# 模型声明
basenn = wf(task='basenn',checkpoint='basenn_act.onnx')
# 待推理数组，此处仅以随机数组为例
data = np.random.random((1, 30, 132)).astype('float32') # 可替换成您想要推理的npz文件路径,如 data = 'action.npz',npz文件中至少应该包括一个键：data,其中存储数据信息（数组形式）。
# 模型推理
res = basenn.inference(data=data)
# 标准化推理结果
result = basenn.format_output(lang="zh")

# 更多用法教程详见：https://xedu.readthedocs.io/zh/master/support_resources/model_convert.html