from pixelarraythirdparty.client import AsyncClient


class CronManagerAsync(AsyncClient):
    async def list_cron_task(self):
        """
        description:
            获取所有配置的定时任务列表，包括任务详情、执行时间、状态等。
        return:
            data(dict): 定时任务列表信息
                - tasks(list): 定时任务列表
                    - id(str): 任务ID
                    - name(str): 任务名称
                    - description(str): 任务描述
                    - schedule(str): 执行时间
                    - enabled(bool): 是否启用
                    - task_name(str): 任务函数名
                    - module_name(str): 模块名
                    - function_name(str): 函数名
                    - file_path(str): 文件路径
                    - parameters(list): 参数列表
                    - task_config(dict): 任务配置
                    - registration_info(dict): 注册信息
                - count(int): 任务数量
                - timestamp(str): 获取时间
            success(bool): 操作是否成功
        """
        data, success = await self._request("GET", "/api/cron/tasks/scheduled")
        if not success:
            return {}, False
        return data, True

    async def get_cron_tasks_detail(self, task_name: str):
        """
        description:
            根据任务名称获取指定任务的详细信息。
        parameters:
            task_name(str): 任务名称
        return:
            data(dict): 任务详细信息
                - task_name(str): 任务名称
                - module_name(str): 模块名
                - function_name(str): 函数名
                - file_path(str): 文件路径
                - description(str): 任务描述
                - parameters(list): 参数列表
                - task_config(dict): 任务配置
                - registration_info(dict): 注册信息
                - timestamp(str): 获取时间
            success(bool): 操作是否成功
        """
        data, success = await self._request("GET", f"/api/cron/tasks/{task_name}")
        if not success:
            return {}, False
        return data, True

    async def trigger_cron_task(self, task_name: str, args: list, kwargs: dict):
        """
        description:
            手动触发指定任务的执行，支持传递参数。
        parameters:
            task_name(str): 任务名称
            args(list): 任务参数列表
            kwargs(dict): 任务关键字参数
        return:
            data(dict): 任务触发信息
                - task_id(str): 任务ID
                - task_name(str): 任务名称
                - status(str): 任务状态，初始为"PENDING"
                - message(str): 触发消息
            success(bool): 操作是否成功
        """
        data, success = await self._request(
            "POST",
            f"/api/cron/tasks/{task_name}/trigger",
            json={"args": args, "kwargs": kwargs},
        )
        if not success:
            return {}, False
        return data, True
