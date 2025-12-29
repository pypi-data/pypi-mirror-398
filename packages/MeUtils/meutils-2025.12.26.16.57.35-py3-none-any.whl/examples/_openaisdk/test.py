import json

import httpx
import jsonpath

from meutils.pipe import storage_to_cookie
from meutils.config_utils.lark_utils import get_spreadsheet_values

storage_state = "/Users/betterme/PycharmProjects/AI/MeUtils/examples/逆向/siliconflow/13003153826.json"
storage_state = get_spreadsheet_values(feishu_url="https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=xlvlrH",
                       to_dataframe=True)[0]

cookie = storage_to_cookie(storage_state[0])

#
# print(cookie)

url = 'https://cloud.siliconflow.cn/api/model/text2img?modelName=stabilityai/stable-diffusion-3-medium&modelSubType=text-to-image'

headers = {
    # 'Accept': '*/*',
    # 'Accept-Language': 'zh-CN,zh;q=0.9',
    # 'Connection': 'keep-alive',
    #
    # 'Content-type': 'application/json',

    'Cookie': cookie,
    # 'Cookie': '_ga=GA1.1.659137215.1719368743; __Host-authjs.csrf-token=e0ef45d98025e394212b732a5fff6a0fb85d413a1b4cc9fb6518f63f7cdd4feb%7C692f34c1ea27fc3d5d97f0c104ee5ee0bcf3d85c1f72a771acbbd6a8df0d39fa; Hm_lvt_85d0fa672fe1e9cf21f0253958808923=1719368752; __Secure-authjs.callback-url=https%3A%2F%2Fcloud.siliconflow.cn; _ga_FS03N2E4YL=GS1.1.1719996062.37.1.1719996174.0.0.0; __Secure-authjs.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwia2lkIjoiZ3dNNWRzR3hqS1RxVnF4cTBrRmVyNElJYy1RMkhRZ01wVUFRSjRsTTkwQzVhZVhmN2RLNlZuOGFHTjlULTBsWVFoYkxiUE9LaEI5a2h3ZmJ6N0Y0NXcifQ..gn04kgduTyVn1dEUn25LYg.v4ZOdSGynGSLVfoe_ka3zwFa1E-clpLNTP4rBMq5b4bw86GqW1OkGM_eU2S9NwPEpFr36qRGLjCfM8P0AW6JDRLEBonyglN-JK2GUReP8he4f1dUPEk_mCbHvXhACSfwAIIL6ymyfBGEZzTJGBlRKnu9mesmFpVIU6b0XN8Gt4c03-l-C4cJ01CcW-m2riQnhjdB8tN7bI2b1K8Tb8mHiHSX_fYFvsZ4W3ChopcsWRUn5VJWmn9JsAgnAb1yrtL8.EufzGdzH-MZmXxPUAqE1HZvgYrwECnwnheMX2BDT084; Hm_lpvt_85d0fa672fe1e9cf21f0253958808923=1719996174',

    # "__Secure-authjs.session-token": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwia2lkIjoiZ3dNNWRzR3hqS1RxVnF4cTBrRmVyNElJYy1RMkhRZ01wVUFRSjRsTTkwQzVhZVhmN2RLNlZuOGFHTjlULTBsWVFoYkxiUE9LaEI5a2h3ZmJ6N0Y0NXcifQ..7L2RBUPZ7n5AvMAjeRYNGw.krz_Vxb-Nk6M_pM-XqxbxxkT1oglmQmkHfbVmB9xMuye5SOtScpWXfCoBc_nPkKXyM3UOmmvndaffD-PY2Sdz4AS91GtQ5pZPKDdDMSMMHHGFmsLjT0keFQKco1AFaFuTelQJ28XJ2RiMC7WObX5iItgU_NfRb2CYGOocjA2DayAI2k7zFXA23AHJrzYvtq_lJlvGs4RLESsI_pH9TGsYs-j5lwdE1dVTmvRoSvjdUwF5oX0xSw8ztw9Xka1M0qx.c4-oPpO11fo9v9871jMmwCyl5HoYueZMrWDjKIoQJe8",
    #
    # "__Host-authjs.csrf-token": "3d0fd54b5ee57d0ea9cbaa0fd4bc903cbf788f7cdf92cecf24a239a452461ee0%7C89d99c34681d489803f182e74511ab87b00625f74e8ca1b7fa1696a7dd060a26",
    # "__Secure-authjs.callback-url": "https%3A%2F%2Fcloud.siliconflow.cn"
    # 'Origin': 'https://cloud.siliconflow.cn',
    # 'Referer': 'https://cloud.siliconflow.cn/models/image/text-to-image',
    # 'Sec-Fetch-Dest': 'empty',
    # 'Sec-Fetch-Mode': 'cors',
    # 'Sec-Fetch-Site': 'same-origin',
    # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    # 'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    # 'sec-ch-ua-mobile': '?0',
    # 'sec-ch-ua-platform': '"macOS"',
}

data = '{"image_size":"1024x1024","batch_size":1,"num_inference_steps":25,"guidance_scale":4.5,"prompt":"Man snowboarding on the mars, ultra high resolution 8k"}'

with httpx.Client(timeout=30) as client:
    response = client.post(url, headers=headers, content=data, follow_redirects=True)

    print(response.cookies)

print(response.text)
