#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/12/22 14:56
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.schemas.video_types import SoraVideoRequest, Video

import replicate


class Tasks(object):

    def __init__(self, base_url: Optional[str] = None, api_key: str = None):
        api_key = api_key or os.getenv("REPLICATE_API_KEY")
        self.client = replicate.client.Client(api_token=api_key)

    async def create(self, request: SoraVideoRequest):

        payload = {
            "prompt": request.prompt,
            "duration": int(request.seconds),
            "resolution": request.resolution,
            "multi_shots": False,
            "negative_prompt": "",
            "enable_prompt_expansion": True,
            # "image": "https://replicate.delivery/pbxt/OF1th8iUuEue0j7p1dces9rrhbss2tri6zIrvWxFSUEAaiVw/replicate-prediction-gbdjrctjksrme0cv4m58vwtdtr.jpg",

        }
        if request.size:
            # if "x" not in request.size:
            #     raise ValueError(f"size must be in format of 1280x720")
            w, h = 16, 9
            if 'x' in request.size:
                w, h = map(int, request.size.split('x'))
            elif ':' in request.size:
                w, h = map(int, request.size.split(':'))
            elif '*' in request.size:
                w, h = map(int, request.size.split('*'))

            if request.resolution in {"720p", None}:
                payload["size"] = "1280*720" if w > h else "720*1280"
            elif request.resolution == "1080p":
                payload["size"] = "1920*1080" if w > h else "1080*1920"

        if request.input_reference:
            request.model = request.model.replace("t2v", "i2v")
            payload["image"] = request.input_reference[0]

        if request.audio:
            payload["audio"] = request.audio

        logany(request)
        logany(bjson(payload))

        response = await self.client.predictions.async_create(
            model=request.model,
            input=payload
        )
        """
        Prediction(id='vzykqfxg2hrmt0cv8khte3g11g', model='wan-video/wan-2.6-i2v', version='hidden', status='starting', input={'duration': 5, 'enable_prompt_expansion': True, 'image': 'https://replicate.delivery/pbxt/OF1th8iUuEue0j7p1dces9rrhbss2tri6zIrvWxFSUEAaiVw/replicate-prediction-gbdjrctjksrme0cv4m58vwtdtr.jpg', 'multi_shots': False, 'negative_prompt': '', 'prompt': 'The vintage clock on the table starts ticking, gears visibly turning inside the glass case, pendulum swinging smoothly, dust particles floating in sunlight beams, close-up macro shot with shallow depth of field.', 'resolution': '720p'}, output=None, logs='', error=None, metrics=None, created_at='2025-12-22T07:08:51.092Z', started_at=None, completed_at=None, urls={'cancel': 'https://api.replicate.com/v1/predictions/vzykqfxg2hrmt0cv8khte3g11g/cancel', 'get': 'https://api.replicate.com/v1/predictions/vzykqfxg2hrmt0cv8khte3g11g', 'stream': 'https://stream.replicate.com/v1/files/jbxs-v3vlgpd4avh5fyfsjinxacrsxb2uj242muyvn4k6jabuljjjfwrq', 'web': 'https://replicate.com/p/vzykqfxg2hrmt0cv8khte3g11g'})

        """

        return response.dict()  # vzykqfxg2hrmt0cv8khte3g11g

    async def get(self, task_id: str):
        response = await self.client.predictions.async_get(task_id)
        #
        logger.debug(bjson(response))

        response = response.dict()
        #
        video = Video(
            id=task_id,
            status=response,

            model=response.get("model"),
            video_url=response.get("output"),

            error=response.get("error")
        )

        # logger.debug(bjson(video))

        return video


if __name__ == '__main__':
    model = "wan-video/wan-2.6-i2v"

    request = SoraVideoRequest(
        model=model,
        # prompt="Put the woman next to the house",
        # prompt="一个裸体女人",
        # prompt='带个墨镜',
        # prompt=prompt,
        # size="2048x2048",

        # aspect_ratio="match_input_image",
        # input_image_1="https://replicate.delivery/pbxt/N7gRAUNcVF6HarL0hdAQA2JYNMlJD52LP1wyaIWRUXWeHzqT/0_1-1.webp",
        # input_image_2="https://replicate.delivery/pbxt/N7gRAK5kbPwdsbOpqgyAIOFQX45U6suTlbL6ws2N74SnGFpo/test.jpg",
        # image="https://s3.ffire.cc/files/jimeng.jpg",
        # image="https://replicate.delivery/pbxt/N7gRAUNcVF6HarL0hdAQA2JYNMlJD52LP1wyaIWRUXWeHzqT/0_1-1.webp"
    )
    print(request)

    # arun(Tasks().create(request))

    task_id = "vzykqfxg2hrmt0cv8khte3g11g"
    arun(Tasks().get(task_id))
