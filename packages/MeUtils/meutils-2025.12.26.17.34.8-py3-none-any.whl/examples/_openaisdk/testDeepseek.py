import asyncio
import aiohttp
import time
import nest_asyncio
import json

baseUrl = "http://localhost:11434/v1/chat/completions"
model = "deepseek-r1:1.5b"
question = "你好，共产党员可以炒股么？"
count = 100
sk = "sk-xxx"


async def send_request(session, baseUrl, model):
    # 设置请求头
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + sk
    }

    # 设置请求参数
    data = {
        'model': model,
        "messages": [
            {"role": "user", "content": question}
        ],
        "stream": True
    }

    # 发送请求
    async with session.post(baseUrl, headers=headers, json=data) as response:
        response.raise_for_status()

        # 测量第一个字的时间
        start_time = time.time()
        async for chunk in response.content:
            if chunk:
                # print(chunk)
                end_time = time.time()
                break
        # 输出第一个字的时间
        print('第一个字的时间:', (end_time - start_time) * 1000)
        return (end_time - start_time) * 1000


async def main(baseUrl, model, count):
    # 创建会话
    async with aiohttp.ClientSession() as session:
        # 创建任务
        tasks = []
        for _ in range(count):
            task = asyncio.ensure_future(send_request(session, baseUrl, model))
            tasks.append(task)

        # 等待所有任务完成
        times = await asyncio.gather(*tasks)
        print(times)
        # 计算平均时间
        avg_time = sum(times) / count

        # 输出平均时间
        print('平均时间:', avg_time)


# 进行测试
loop = asyncio.get_event_loop()
loop.run_until_complete(main(baseUrl, model, count))
