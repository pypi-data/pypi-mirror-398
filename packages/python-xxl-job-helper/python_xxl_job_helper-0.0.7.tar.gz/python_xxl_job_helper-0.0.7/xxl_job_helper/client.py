# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-xxl-job-helper
# FileName:     client.py
# Description:  客户端模块
# Author:       ASUS
# CreateDate:   2025/12/22
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import json
from typing import Optional, Dict, Any
from http_helper.client.async_proxy import HttpClientFactory


class XxlJobClient:

    def __init__(
            self, *, domain: str, protocol: str, token: str, timeout: Optional[int] = None, retry: Optional[int] = None,
            enable_log: Optional[bool] = None,
    ) -> None:
        self._token = token
        self._domain = domain or "127.0.0.1:18070"
        self._protocol = protocol or "http"
        self._origin = f"{self._protocol}://{self._domain}"
        self._timeout = timeout or 60
        self._retry = retry or 1
        self._enable_log = enable_log or True
        self.http_client: Optional[HttpClientFactory] = None

    def _get_http_client(self):
        """延迟获取 HTTP 客户端"""
        if self.http_client is None:
            self.http_client = HttpClientFactory(
                protocol=self._protocol,
                domain=self._domain,
                timeout=self._timeout or 60,
                retry=self._retry or 1,
                enable_log=self._enable_log if self._enable_log is not None else True,
            )
        return self.http_client

    def _get_headers(self) -> Dict[str, str]:
        return {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "cookie": self._token,
            "host": self._domain,
            "origin": self._origin,
            "referer": f"{self._origin}/xxl-job-admin/jobinfo",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"

        }

    async def get_task_group(
            self, task_group_name: Optional[str] = None, is_end: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        获取任务组，即执行器管理列表
        :param task_group_name: 执行器名称
        :param is_end: 是否为最后一次调用
        :return:
        """
        # 获取客户端
        http_client = self._get_http_client()

        # 获取头部
        headers = self._get_headers()

        url_suffux: str = "/xxl-job-admin/jobgroup/pageList"
        headers["referer"] = self._origin + url_suffux
        data: Dict[str, Any] = {
            "offset": 0,
            "pagesize": 100,
            "title": ""
        }
        if task_group_name:
            data["title"] = task_group_name
        response = await http_client.request(
            method="post",
            url=url_suffux,
            data=data,
            headers=headers,
            is_end=is_end if is_end is not None else True,
        )
        if task_group_name:
            if response.get("data") and isinstance(response.get("data"), dict):
                response_data = response.get("data")
                executors = response_data.get("data")
                if executors and isinstance(executors, list):
                    response["data"] = executors[0]
        return response

    @staticmethod
    def _get_task_info_url_suffux() -> str:
        return "/xxl-job-admin/jobinfo/pageList"

    async def get_task_info(
            self, task_group_id: int, task_desc: Optional[str] = None, is_end: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        获取任务信息，即任务管理列表
        :param task_group_id: 任务组ID
        :param task_desc: 任务描述
        :param is_end: 是否为最后一次调用
        :return:
        """
        # 获取客户端
        http_client = self._get_http_client()

        # 获取头部
        headers = self._get_headers()

        url_suffux: str = self._get_task_info_url_suffux()
        headers["referer"] = self._origin + url_suffux
        data: Dict[str, Any] = {
            "jobGroup": task_group_id,
            "triggerStatus": -1,
            "offset": 0,
            "pagesize": 100,
            "jobDesc": "",
            "executorHandler": "",
            "author": ""
        }
        if task_desc:
            data["jobDesc"] = task_desc
        response = await http_client.request(
            method="post",
            url=url_suffux,
            data=data,
            headers=headers,
            is_end=is_end if is_end is not None else True,
        )
        if task_desc:
            if response.get("data") and isinstance(response.get("data"), dict):
                response_data = response.get("data")
                jobs = response_data.get("data")
                if jobs and isinstance(jobs, list):
                    response["data"] = jobs[0]
        return response

    async def _update_task_triger(
            self, task_id: int, task_param: Optional[Dict[str, Any]] = None, is_end: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        更新任务triger
        :param task_id: 任务ID
        :param task_param: 任务执行参数
        :param is_end: 是否为最后一次调用
        :return:
        """
        # 获取客户端
        http_client = self._get_http_client()

        # 获取头部
        headers = self._get_headers()

        headers["referer"] = self._origin + self._get_task_info_url_suffux()
        data: Dict[str, Any] = {
            "id": task_id,
            "executorParam": "",
            "addressList": ""
        }
        if task_param:
            data["executorParam"] = json.dumps(task_param)
        return await http_client.request(
            method="post",
            url="/xxl-job-admin/jobinfo/trigger",
            data=data,
            headers=headers,
            is_end=is_end if is_end is not None else True,
        )

    async def update_task_triger(
            self, task_group_name: str, task_desc: str, task_param: Optional[Dict[str, Any]] = None
    ) -> None:
        response = await self.get_task_group(task_group_name=task_group_name, is_end=False)
        if response.get("code") == 200 and response.get("data"):
            task_group_id = response.get("data").get("id")
        else:
            raise RuntimeError(response.get("msg"))
        response = await self.get_task_info(task_group_id=task_group_id, task_desc=task_desc, is_end=False)
        if response.get("code") == 200 and response.get("data"):
            task_id = response.get("data").get("id")
        else:
            raise RuntimeError(response.get("msg"))
        response = await self._update_task_triger(task_id=task_id, task_param=task_param)
        if response.get("code") != 200:
            raise RuntimeError(response.get("msg"))

    async def close(self):
        """关闭客户端连接"""
        if self.http_client:
            await self.http_client.close()


if __name__ == '__main__':
    import asyncio

    domain = "192.168.3.240:18070"
    protocol = "http"
    token = "xxl_job_login_token=eyJ1c2VySWQiOiIxIiwiZXhwaXJlVGltZSI6MCwic2lnbmF0dXJlIjoiMDRjOTA0YzRlYTk1NGI5YTg4MzcyZDU4MDU2NmVhZWYifQ; JSESSIONID=8FE12B7BDF8B5A31123B5B29A00C187B"

    xxl_client = XxlJobClient(protocol=protocol, domain=domain, token=token)
    # print(asyncio.run(xxl_client.get_task_group(task_group_name="东航官网自动出票")))
    # print(asyncio.run(xxl_client.get_task_group(task_group_name="")))
    # print(asyncio.run(xxl_client.get_task_info(task_group_id=4, task_desc="")))
    # print(asyncio.run(xxl_client.get_task_info(task_group_id=4, task_desc="抓单")))
    executor_param = {
        "qlv_user_id": "周汗林",
        "policy": "MU",
        "retry": 1,
        "timeout": 60,
        "last_time_ticket": 1800
    }
    print(asyncio.run(xxl_client.update_task_triger(
        task_group_name="东航官网自动出票", task_desc="抓单", task_param=executor_param
    )))
