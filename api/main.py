from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import time
import json
import os

app = FastAPI()

# 完美跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EventRequest(BaseModel):
    raw_text: str

@app.post("/api/parse_event")
async def parse_event(request: EventRequest):
    # ⚠️ 填入你真实的 API Key
 api_key = os.environ.get("DASHSCOPE_API_KEY") 
    
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    # 极其严苛的 Prompt，强制 AI 吐出干净的 JSON
    prompt = f"""你是一个大学生日程规划助手。请分析以下文本，提取事件信息。
【注意】如果文本中完全没有提到时间，请将 day_index 设为 1（周一），period_index 设为 1（第1节）。
你必须且只能输出以下 JSON 格式，不要包含任何其他文字、解释或 markdown 标记：
{{"event": "事件名称", "time": "具体时间", "location": "地点", "importance": "高/中/低", "advice": "建议", "day_index": 1到7的数字, "period_index": 1到13的数字}}
文本内容：{request.raw_text}"""

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "qwen-plus", 
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        # 加入 timeout=20，防止无限卡死
        response = requests.post(url, headers=headers, json=data, timeout=20)
        
        if response.status_code != 200:
            print("\\n============== 阿里云报错 ==============")
            print(response.text)
            print("========================================\\n")
            raise HTTPException(status_code=500, detail="AI接口返回错误")
        
        ai_result = response.json()["choices"][0]["message"]["content"]
        return {"result": ai_result}
        
    except requests.exceptions.Timeout:
        print("\\n=== 请求超时，可能是网络问题或 Key 没开通 ===\\n")
        raise HTTPException(status_code=500, detail="网络超时")
    except Exception as e:
        print("\\n=== 代码异常 ===\\n", str(e))
        raise HTTPException(status_code=500, detail="代码异常")

 handler = app