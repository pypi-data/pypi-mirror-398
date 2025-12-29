#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/10/17 22:55
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.schemas.video_types import SoraVideoRequest, Video
from meutils.apis.volcengine_apis import videos as volc_videos
from meutils.apis.aiml import videos as aiml_videos
from meutils.apis.gitee import videos as gitee_videos

from meutils.apis.runware import videos as runware_videos  # todo 兼容
from meutils.apis.replicate import videos as replicate_videos  # todo 兼容


class OpenAIVideos(object):

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or ""
        logger.debug(f"base_url: {self.base_url}")  # 来源

    @cached_property
    def biz(self):
        parts = self.base_url.split(".")
        return (parts[1] if len(parts) >= 2 else self.base_url)[::-1]

    async def create(self, request: SoraVideoRequest):
        response = {}
        if any(i in self.base_url for i in {"gitee", "moark"}):
            response = await gitee_videos.Tasks(api_key=self.api_key).create(request)

        elif "volc" in self.base_url:
            response = await volc_videos.create_task(request, self.api_key)  # {'id': 'cgt-20250611152553-r46ql'}

        elif "aimlapi" in self.base_url:
            response = await aiml_videos.Tasks(api_key=self.api_key, base_url=self.base_url).create(request)

        elif "replicate" in self.base_url:
            response = await replicate_videos.Tasks(api_key=self.api_key).create(request)

        if task_id := (
                response.get("id")
                or response.get("task_id")
                or response.get("generation_id")
        ):
            task_id = task_id.replace("/", "@")
            # task_id = f"{self.biz}::{task_id}"  # 组装biz # todo base url  # 区分不同平台
            if self.api_key:
                await redis_aclient.set(task_id, self.api_key, ex=7 * 34 * 3600)

            return Video(id=task_id)

    async def get(self, task_id):
        video = Video(id=task_id)
        if api_key := await redis_aclient.get(task_id):
            api_key = api_key.decode()
        else:
            raise ValueError(f"task_id not found")

        task_id = task_id.replace("@", "/")  # 还原

        if api_key.startswith("r8_"):
            video = await replicate_videos.Tasks(api_key=self.api_key, base_url=self.base_url).get(task_id)
            return video

        elif len(api_key) == 40 and api_key.isupper():
            video = await gitee_videos.Tasks(api_key=self.api_key, base_url=self.base_url).get(task_id)
            return video

        elif task_id.startswith("cgt-"):
            if response := await volc_videos.get_task(task_id, api_key):
                # logger.debug(bjson(response))
                """
                {
                    "id": "cgt-20251225095015-5xmc2",
                    "model": "doubao-seedance-1-0-pro-250528",
                    "status": "failed",
                    "error": {
                        "code": "OutputVideoSensitiveContentDetected",
                        "message": "The request failed because the output video may contain sensitive information. Request id: 02176662741563700000000000000000000ffffac19188dffe699"
                    },
                    "created_at": 1766627415,
                    "updated_at": 1766627466,
                    "service_tier": "default",
                    "execution_expires_after": 172800
                }
                """

                video = Video(id=task_id, status=response, error=response.get("error"), metadata=response, )
                if video.status == "completed":
                    video.progress = 100
                    video.video_url = response.get("content", {}).get("video_url")  # 多个是否兼容

        elif len(api_key) == 32 and (":" in task_id and "/" in task_id or len(task_id) == 21):  # 粗判断
            video = await aiml_videos.Tasks(api_key=api_key, base_url=self.base_url).get(task_id)
            return video

        elif len(api_key) == 32 and len(task_id) == 36:  # 粗判断
            video = await runware_videos.get_task(task_id)
            return video

        return video


if __name__ == '__main__':
    api_key = "267a3b8a-ef06-4d8f-bd24-150f99bb17c1"
    model = "doubao-seedance-1-0-pro-fast-251015"

    api_key = "603051fc1d7e49e19de2c67521d4a30e"
    model = "openai/sora-2-t2v"
    model = "alibaba/wan2.5-i2v-preview"
    request = SoraVideoRequest(
        # model=model,
        model=f"{model}_480p",
        # model=f"{model}_720p",
        # model=f"{model}_1080p",

        # seconds="4",
        size="720x1280",
    )
    videos = OpenAIVideos(api_key=api_key)

    # video = arun(videos.create(request))

    # Video(id='cgt-20251031183121-zrt26', completed_at=None, created_at=1761906681, error=None, expires_at=None,
    #       model=None, object='video', progress=0, remixed_from_video_id=None, seconds=None, size=None, status='queued',
    #       video_url=None, metadata=None)

    task_id = "7e726e6f-e9b1-40b3-b894-fec2d1274c53:alibaba@wan2.5-t2v-preview"
    arun(videos.get(task_id))

    # video = arun(videos.create(request))

    # task_id = "video_690dc20970808198b65cd9c04205edce0ed7e02d84c9579c:openai/sora-2-t2v"
    # task_id = "ee57044b-01e8-4aea-bd5f-48a03d653548:alibaba/wan2.5-t2v-preview"
    # task_id = "df489658-125b-4c65-a949-41d73c76cf0e:alibaba/wan2.5-t2v-preview"
    # arun(videos.get(task_id))

    # wJCWwQ5x0CcVIWGzXEp-A
