from pixelarraythirdparty.client import AsyncClient
from typing import List, Optional, Union, BinaryIO
import aiohttp
import os
import mimetypes


class FeedbackManagerAsync(AsyncClient):
    async def create_feedback(
        self,
        project_id: int,
        content: str,
        contact_info: str,
        images: Optional[List[Union[str, BinaryIO, bytes]]] = None,
        video: Optional[Union[str, BinaryIO, bytes]] = None,
    ):
        """
        description:
            创建新的客户反馈，反馈必须关联一个项目。支持上传图片和视频文件。
        parameters:
            project_id(int): 项目ID，必须关联一个已存在的项目
            content(str): 反馈内容
            contact_info(str): 反馈人联系方式
            images(List[Union[str, BinaryIO, bytes]], optional): 图片文件列表，可以是文件路径、文件对象或字节数据，最多9张
            video(Union[str, BinaryIO, bytes], optional): 视频文件，可以是文件路径、文件对象或字节数据，最多1个
        return:
            data(dict): 反馈信息
                - id(int): 反馈ID
                - project_id(int): 项目ID
                - content(str): 反馈内容
                - contact_info(str): 反馈人联系方式
                - created_at(str): 反馈创建时间
            success(bool): 操作是否成功
        """
        # 先创建反馈
        data = {
            "project_id": project_id,
            "content": content,
            "contact_info": contact_info,
        }
        feedback_data, success = await self._request("POST", "/api/feedback/create", json=data)
        if not success:
            return {}, False
        
        feedback_id = feedback_data.get("id")
        if not feedback_id:
            return feedback_data, True
        
        # 如果有文件需要上传，则上传文件
        if images or video:
            # 上传图片
            if images:
                if len(images) > 9:
                    return {}, False  # 图片数量超过限制
                for image in images:
                    await self._upload_file(feedback_id, image, "image")
            
            # 上传视频
            if video:
                await self._upload_file(feedback_id, video, "video")
        
        return feedback_data, True
    
    async def _upload_file(
        self,
        feedback_id: int,
        file_data: Union[str, BinaryIO, bytes],
        file_type: str,
    ):
        """
        description:
            内部方法：上传文件到OSS
        parameters:
            feedback_id(int): 反馈ID
            file_data(Union[str, BinaryIO, bytes]): 文件数据，可以是文件路径、文件对象或字节数据
            file_type(str): 文件类型，可选值："image"（图片）、"video"（视频）
        return:
            success(bool): 上传是否成功
        """
        # 读取文件数据
        file_content = None
        file_name = None
        file_size = None
        mime_type = None
        
        if isinstance(file_data, str):
            # 文件路径
            file_name = os.path.basename(file_data)
            with open(file_data, "rb") as f:
                file_content = f.read()
            file_size = len(file_content)
            mime_type, _ = mimetypes.guess_type(file_data)
        elif isinstance(file_data, bytes):
            # 字节数据
            file_name = f"file.{file_type}"
            file_content = file_data
            file_size = len(file_content)
        else:
            # 文件对象
            file_name = getattr(file_data, "name", None) or getattr(file_data, "filename", f"file.{file_type}")
            try:
                # 尝试异步读取
                if hasattr(file_data, "read"):
                    read_method = file_data.read
                    # 检查是否是协程函数
                    import inspect
                    if inspect.iscoroutinefunction(read_method):
                        file_content = await read_method()
                    else:
                        file_content = read_method()
                else:
                    file_content = file_data
            except Exception as e:
                print(f"读取文件对象失败: {str(e)}")
                return False
            file_size = len(file_content) if file_content else 0
            mime_type, _ = mimetypes.guess_type(file_name)
        
        if not file_content:
            return False
        
        # 获取上传签名链接
        upload_data = {
            "feedback_id": feedback_id,
            "file_name": file_name,
            "file_type": file_type,
        }
        if file_size:
            upload_data["file_size"] = file_size
        if mime_type:
            upload_data["mime_type"] = mime_type
        
        upload_info, success = await self._request(
            "POST", "/api/feedback/files/upload/presigned-url", json=upload_data
        )
        if not success:
            return False
        
        presigned_url = upload_info.get("presigned_url")
        oss_path = upload_info.get("oss_path")
        
        if not presigned_url:
            return False
        
        # 上传文件到OSS
        try:
            headers = {}
            if mime_type:
                headers["Content-Type"] = mime_type
            
            async with aiohttp.ClientSession() as session:
                async with session.put(presigned_url, data=file_content, headers=headers) as resp:
                    if resp.status not in [200, 204]:
                        return False
        except Exception as e:
            print(f"上传文件到OSS失败: {str(e)}")
            return False
        
        # 调用上传完成接口
        complete_data = {
            "feedback_id": feedback_id,
            "oss_path": oss_path,
            "file_name": file_name,
            "file_type": file_type,
        }
        if file_size:
            complete_data["file_size"] = file_size
        if mime_type:
            complete_data["mime_type"] = mime_type
        
        _, success = await self._request(
            "POST", "/api/feedback/files/upload/complete", json=complete_data
        )
        return success

    async def list_feedback(
        self,
        page: int = 1,
        page_size: int = 10,
        project_id: int = None,
    ):
        """
        description:
            分页查询反馈列表，支持按项目ID进行筛选。
        parameters:
            page(int): 页码
            page_size(int): 每页数量
            project_id(int): 项目ID筛选，可选
        return:
            data(dict): 反馈列表信息
                - feedbacks(list): 反馈列表
                    - id(int): 反馈ID
                    - project_id(int): 项目ID
                    - project_name(str): 项目名称
                    - content(str): 反馈内容
                    - contact_info(str): 反馈人联系方式
                    - created_at(str): 反馈创建时间
                - total(int): 总反馈数量
                - page(int): 当前页码
                - page_size(int): 每页数量
            success(bool): 操作是否成功
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if project_id is not None:
            params["project_id"] = project_id
        data, success = await self._request("GET", "/api/feedback/list", params=params)
        if not success:
            return {}, False
        return data, True

    async def get_feedback_detail(self, feedback_id: int):
        """
        description:
            根据反馈ID获取反馈的详细信息。如果反馈中包含图片和视频，返回的文件信息会包含预览签名链接。
        parameters:
            feedback_id(int): 反馈ID
        return:
            data(dict): 反馈详细信息
                - id(int): 反馈ID
                - project_id(int): 项目ID
                - project_name(str): 项目名称
                - content(str): 反馈内容
                - contact_info(str): 反馈人联系方式
                - created_at(str): 反馈创建时间
                - files(list, optional): 文件列表，如果反馈包含文件
                    - id(int): 文件ID
                    - feedback_id(int): 反馈ID
                    - oss_path(str): OSS存储路径
                    - file_name(str): 文件名
                    - file_type(str): 文件类型（"image"或"video"）
                    - file_size(int, optional): 文件大小（字节）
                    - mime_type(str, optional): MIME类型
                    - presigned_url(str): 预览签名链接，有效期1小时
            success(bool): 操作是否成功
        """
        data, success = await self._request("GET", f"/api/feedback/{feedback_id}")
        if not success:
            return {}, False
        return data, True

    async def delete_feedback(self, feedback_id: int):
        """
        description:
            根据反馈ID删除指定的反馈记录。仅管理员可删除反馈。
        parameters:
            feedback_id(int): 反馈ID
        return:
            data(None): 删除成功时返回None
            success(bool): 操作是否成功
        """
        data, success = await self._request("DELETE", f"/api/feedback/{feedback_id}")
        if not success:
            return {}, False
        return data, True

