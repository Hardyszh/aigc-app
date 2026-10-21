from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import base64
import re
import time
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class EventRequest(BaseModel):
    raw_text: str

class ImageRequest(BaseModel):
    image_base64: str

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "如果你本地测试可以临时写在这里")

@app.post("/api/parse_event")
async def parse_event(request: EventRequest):
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    prompt = f"""你是一个大学生日程规划助手。请分析以下杂乱的文本，提取出所有的事件、时间、地点和重要性。
同时，请根据时间推断该事件在课表中的位置。
严格按照以下JSON格式输出，不要输出任何其他文字：
{{"event": "事件名称", "time": "具体时间", "location": "地点", "importance": "高/中/低", "advice": "建议", "day_index": 数字(周一为1, 周二为2...周五为5), "period_index": 数字(上午为1或2, 下午为5或6, 晚上为8或9)}}
文本内容：{request.raw_text}"""

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "qwen-vl-ocr-2025-11-20", 
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print("文本接口报错：", response.text)
        raise HTTPException(status_code=500, detail="AI接口调用失败")
    
    ai_result = response.json()["choices"][0]["message"]["content"]
    return {"result": ai_result}


@app.post("/api/parse_image")
async def parse_image(request: ImageRequest):
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    # 核心绝招：让 AI 输出 Markdown 表格，不要输出 JSON
    prompt = """请仔细观察这张大学课表图片。
    请严格根据图片的网格结构，输出一个 Markdown 格式的表格。
    要求：
    1. 表头依次为：节次 | 星期一 | 星期二 | 星期三 | 星期四 | 星期五 | 星期六 | 星期日。
    2. 左侧第一列写节次（1, 2, 3...）。
    3. 每一格里填写课程名称。如果这一格是空的，请留空。
    4. 如果一节课跨越了多个格子，请在每一个格子里都写上这门课的名字（例如，连上三节的高数，在1、2、3节对应的格子里都写上“高等数学”）。
    5. 不需要输出任何多余的解释，直接输出 Markdown 表格。"""
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "qwen-vl-plus", # 如果开通了 qwen-vl-max，强烈建议换成 max，准确率飙升
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{request.image_base64}"}}
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="AI接口调用失败")
    
    ai_text = response.json()["choices"][0]["message"]["content"]
    print("----- AI 返回的表格 -----")
    print(ai_text) # 你可以在终端里看看 AI 画表画得对不对
    
    # =======================================================
    # 💡 下面这段代码，是把 AI 画的 Markdown 表格，强行转成你的前端需要的 JSON
    # =======================================================
    courses = []
    
    # 提取所有表格行
    lines = [line.strip() for line in ai_text.split('\n') if line.strip().startswith('|')]
    
    # 跳过表头和分割线（类似 |---|---| 的行）
    data_lines = []
    for line in lines:
        if '节次' in line or '---' in line:
            continue
        data_lines.append(line)
        
    colors = ['#ff9e9e', '#7fb3ff', '#59d1b1', '#f8b660', '#b3e19d', '#e6a23c']
    
    # 遍历每一行（每一节课）
    for period_idx, line in enumerate(data_lines):
        period = period_idx + 1 # 第几节 (1-12)
        # 按 '|' 切分单元格
        cells = [c.strip() for c in line.split('|')[1:-1]]
        
        if len(cells) < 8: continue # 格式不标准跳过
        
        # 遍历每一天 (周一到周日，对应索引 1 到 7)
        for day_idx in range(1, 8):
            course_name = cells[day_idx]
            
            if course_name and course_name != '' and course_name != '无':
                # 去除可能的 HTML 标签和多余空格
                course_name = re.sub(r'<[^>]+>', '', course_name)
                
                # 判断是不是同一个课连续上
                # (简单处理：如果是同一个名字，且前一个节次刚加过，就合并 span)
                merged = False
                if period > 1:
                    # 找找看前一节课是不是同一天的同一门课
                    prev_course = next((c for c in courses if c['day'] == day_idx and c['startPeriod'] + c['span'] - 1 == period - 1), None)
                    if prev_course and prev_course['name'] == course_name:
                        prev_course['span'] += 1 # 延长跨度
                        merged = True
                
                if not merged:
                    courses.append({
                        "name": course_name,
                        "day": day_idx,
                        "startPeriod": period,
                        "span": 1,
                        "room": "见课表", # 因为画表格没提教室，这里给个默认值
                        "teacher": "",
                        "color": colors[(day_idx + period) % len(colors)]
                    })

    import json
    return {"result": json.dumps(courses, ensure_ascii=False)}