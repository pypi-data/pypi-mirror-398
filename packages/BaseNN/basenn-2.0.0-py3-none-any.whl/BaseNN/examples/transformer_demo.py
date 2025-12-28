import transformers
from transformers import pipeline
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def sa(path):
    input_context = 'fuck'
    print(input_context)
    print(pipeline('sentiment-analysis',path)(input_context))
    input_context = 'you are fucking good '
    print(input_context)
    print(pipeline('sentiment-analysis',path)(input_context))
    input_context = '草'
    print(input_context)
    print(pipeline('sentiment-analysis',path)(input_context))
    input_context = '青草 '
    print(input_context)
    print(pipeline('sentiment-analysis',path)(input_context))

def download_model(path):
    from openxlab.model import download
    import os
    if not os.path.exists(path):
        os.mkdir(path)
    model_name = [
        "pytorch_model.bin",
        "model.safetensors",
        "vocab.txt",
        "tokenizer_config.json",
        "config.json"
    ]
    download('test12318/bert-english',model_name =model_name,output=path)

def llama2():
    ckpt = "/home/user/下载/Llama-2-7b-chat-hf"
    # Use a pipeline as a high-level helper
    from transformers import pipeline
    pipe = pipeline("text-generation"  , model=ckpt)
    print(pipe("今天天气如何"))
    # tokenizer = AutoTokenizer.from_pretrained(ckpt)
    # model = AutoModelForCausalLM.from_pretrained(ckpt, trust_remote_code=True, torch_dtype=torch.float16)

    # input_context = "今天天气如何"
    # input_ids = tokenizer.encode(input_context, return_tensors="pt")
    # output = model.generate(input_ids, max_length=128, temperature=0.7)
    # output_text = tokenizer.decode(output[0], skip_special_tokens=True)
    # print(output_text)

if __name__=="__main__":
    # llama2()
    path = 'bert-xlab-1'
    # download_model(path)
    # sa(path)
    llama2()