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
from xxl_job_helper.utils import cron_last_seconds
from http_helper.client.async_proxy import HttpClientFactory


class XxlJobClient:

    def __init__(
            self, *, domain: str, protocol: str, token: Optional[str] = None, timeout: Optional[int] = None,
            retry: Optional[int] = None, enable_log: Optional[bool] = None,
    ) -> None:
        self._token = token
        self._domain = domain or "127.0.0.1:18070"
        self._protocol = protocol or "http"
        self._origin = f"{self._protocol}://{self._domain}"
        self._timeout = timeout or 60
        self._retry = retry or 1
        self._enable_log = enable_log or True
        self.http_client: Optional[HttpClientFactory] = None

    @property
    def token(self) -> str:
        return self._token

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
        headers = {
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "host": self._domain,
            "origin": self._origin,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest"

        }
        if self._token:
            headers["cookie"] = f"xxl_job_login_token={self._token}"
        return headers

    @classmethod
    def get_login_url(cls) -> str:
        return "/xxl-job-admin/auth/login"

    async def do_login(self, username: str, password: str, is_end: Optional[bool] = None) -> Dict[str, Any]:
        """
        登录xxl-job
        :param username: 用户名
        :param password: 密码
        :param is_end: 是否为最后一次调用
        :return:
        """
        # 获取客户端
        http_client = self._get_http_client()

        # 获取头部
        headers = self._get_headers()

        url_suffux: str = "/xxl-job-admin/auth/doLogin"
        headers["referer"] = self._origin + self.get_login_url()
        data: Dict[str, Any] = {
            "userName": username,
            "password": password
        }
        response = await http_client.request(
            method="post",
            url=url_suffux,
            data=data,
            headers=headers,
            is_end=is_end if is_end is not None else True,
            has_cookie=True
        )
        cookies = response.pop("cookies", None)
        if cookies:
            response["data"] = self._token = cookies.split(";")[0].split("=")[-1]
        return response

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

    async def _schedule_triger(
            self, task_id: int, task_param: Optional[Dict[str, Any]] = None, is_end: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        调度执行一次任务triger
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

    async def _start_task(self, task_id: str, is_end: Optional[bool] = None) -> Dict[str, Any]:
        # 获取客户端
        http_client = self._get_http_client()

        # 获取头部
        headers = self._get_headers()

        headers["referer"] = self._origin + self._get_task_info_url_suffux()
        data: Dict[str, Any] = {
            "ids[]": task_id
        }
        return await http_client.request(
            method="post",
            url="/xxl-job-admin/jobinfo/start",
            data=data,
            headers=headers,
            is_end=is_end if is_end is not None else True,
        )

    async def start_task(
            self, *, task_group_name: str, task_desc: str, author: str, alarm_email: str, delay: int,
            schedule_conf: str, executor_handler: str, task_param: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
        response = await self._update_triger(
            task_group_id=task_group_id, task_desc=task_desc, task_id=task_id, author=author, alarm_email=alarm_email,
            delay=delay, schedule_conf=schedule_conf, executor_handler=executor_handler,
            task_param=task_param, is_end=False
        )
        if response.get("code") != 200:
            raise RuntimeError(response.get("msg"))
        response = await self._start_task(task_id=task_id, is_end=True)
        if response.get("code") != 200:
            raise RuntimeError(response.get("msg"))
        return response

    async def _update_triger(
            self, *, task_group_id: int, task_desc: str, task_id: int, author: str, alarm_email: str, delay: int,
            schedule_conf: str, executor_handler: str, task_param: Optional[Dict[str, Any]] = None,
            is_end: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        更新任务triger
        :param task_group_id: 任务组ID
        :param task_desc: 任务描述
        :param task_id: 任务ID
        :param author: 维护者
        :param alarm_email: 接收告警的电子邮箱
        :param delay: 延迟
        :param schedule_conf: 任务出发的cron时间
        :param executor_handler: 任务执行函数
        :param task_param: 任务执行参数
        :param is_end: 是否为最后一次调用
        :return:
        """
        # 获取客户端
        http_client = self._get_http_client()

        # 获取头部
        headers = self._get_headers()

        headers["referer"] = self._origin + self._get_task_info_url_suffux()
        schedule_conf_cron = cron_last_seconds(cron=schedule_conf, seconds=delay)
        data: Dict[str, Any] = {
            "jobGroup": task_group_id,
            "jobDesc": task_desc,
            "author": author,
            "alarmEmail": alarm_email,
            "scheduleType": "CRON",
            "scheduleConf": schedule_conf,
            "cronGen_display": schedule_conf,
            "schedule_conf_CRON": schedule_conf_cron,
            "schedule_conf_FIX_RATE": "",
            "schedule_conf_FIX_DELAY": "",
            "executorHandler": executor_handler,
            "executorParam": "",
            "executorRouteStrategy": "FIRST",
            "childJobId": "",
            "misfireStrategy": "DO_NOTHING",
            "executorBlockStrategy": "SERIAL_EXECUTION",
            "executorTimeout": 0,
            "executorFailRetryCount": 0,
            "id": task_id
        }
        if task_param:
            data["executorParam"] = json.dumps(
                task_param,
                ensure_ascii=False,
                indent=4,
                sort_keys=False
            )
        return await http_client.request(
            method="post",
            url="/xxl-job-admin/jobinfo/update",
            data=data,
            headers=headers,
            is_end=is_end if is_end is not None else True,
        )

    async def update_triger(
            self, *, task_group_name: str, task_desc: str, author: str, alarm_email: str, delay: int,
            schedule_conf: str, executor_handler: str, task_param: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
        response = await self._update_triger(
            task_group_id=task_group_id, task_desc=task_desc, task_id=task_id, author=author, alarm_email=alarm_email,
            delay=delay, schedule_conf=schedule_conf, executor_handler=executor_handler,
            task_param=task_param, is_end=True
        )
        if response.get("code") != 200:
            raise RuntimeError(response.get("msg"))
        return response

    async def schedule_triger(
            self, task_group_name: str, task_desc: str, task_param: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
        response = await self._schedule_triger(task_id=task_id, task_param=task_param)
        if response.get("code") != 200:
            raise RuntimeError(response.get("msg"))
        return response

    async def close(self):
        """关闭客户端连接"""
        if self.http_client:
            await self.http_client.close()


if __name__ == '__main__':
    import asyncio

    domain = "192.168.3.240:18070"
    protocol = "http"

    kwargs = {
        "task_group_name": "东航官网自动出票",
        "task_desc": "劲旅抓单",
        "delay": 30,
        "schedule_conf": "12 12 16 23 12 ? 2025",
        "executor_handler": "fetch_unticketed_order",
        "author": "周汗林",
        "alarm_email": "ckf10000@sina.com",
        "token": "xxl_job_login_token=eyJ1c2VySWQiOiIxIiwiZXhwaXJlVGltZSI6MCwic2lnbmF0dXJlIjoiMDRjOTA0YzRlYTk1NGI5YTg4MzcyZDU4MDU2NmVhZWYifQ; JSESSIONID=8FE12B7BDF8B5A31123B5B29A00C187B",
        "task_param": {
            "qlv_user_id": "周汗林",
            "policy": "MU",
            "retry": 1,
            "timeout": 60,
            "last_time_ticket": 1800
        }
    }

    # xxl_client = XxlJobClient(protocol=protocol, domain=domain, token=kwargs.get("token"))
    # print(asyncio.run(xxl_client.get_task_group(task_group_name="东航官网自动出票")))
    # print(asyncio.run(xxl_client.get_task_group(task_group_name="")))
    # print(asyncio.run(xxl_client.get_task_info(task_group_id=4, task_desc="")))
    # print(asyncio.run(xxl_client.get_task_info(task_group_id=4, task_desc="抓单")))
    # print(asyncio.run(xxl_client.schedule_triger(
    #     task_group_name=kwargs.get("task_group_name"), task_desc=kwargs.get("task_desc"), task_param=kwargs
    # )))
    # print(asyncio.run(xxl_client.update_triger(
    #     task_group_name=kwargs.get("task_group_name"), task_desc=kwargs.get("task_desc"), author=kwargs.get("author"),
    #     alarm_email=kwargs.get("alarm_email"), delay=kwargs.get("delay"),
    #     schedule_conf=kwargs.get("schedule_conf"),
    #     executor_handler="fetch_unticketed_order", task_param=kwargs,
    # )))

    # print(asyncio.run(xxl_client.start_task(
    #     task_group_name=kwargs.get("task_group_name"), task_desc=kwargs.get("task_desc"), author=kwargs.get("author"),
    #     alarm_email=kwargs.get("alarm_email"), delay=kwargs.get("delay"),
    #     schedule_conf=kwargs.get("schedule_conf"),
    #     executor_handler="fetch_unticketed_order", task_param=kwargs,
    # )))
    xxl_client = XxlJobClient(protocol=protocol, domain=domain)
    print(asyncio.run(xxl_client.do_login(username="ceair001", password="ceair001")))
