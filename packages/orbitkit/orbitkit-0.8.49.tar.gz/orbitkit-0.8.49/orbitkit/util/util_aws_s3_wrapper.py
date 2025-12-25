import logging
import os.path
from typing import Optional
import boto3
from orbitkit.util import get_from_dict_or_env, s3_split_path, get_content_type_4_filename
import botocore
from botocore.exceptions import ClientError
import aioboto3
import aiofiles

logger = logging.getLogger(__name__)


class AwsS3Wrapper:
    """Encapsulates Amazon s3 actions for Orbitfin"""

    def __init__(self, s3_resource, s3_client):
        """
        :param s3_resource: boto3.resource('s3')
        :param s3_client: boto3.client('s3')
        """
        self.s3_resource = s3_resource
        self.s3_client = s3_client

    @classmethod
    def from_s3(cls, *args, **kwargs):
        # Try to get key aws pair
        aws_access_key_id = get_from_dict_or_env(
            kwargs, "aws_access_key_id", "AWS_ACCESS_KEY_ID",
        )

        aws_secret_access_key = get_from_dict_or_env(
            kwargs, "aws_secret_access_key", "AWS_SECRET_ACCESS_KEY",
        )

        s3_resource = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

        return cls(s3_resource, s3_client)

    def get_s3_resource(self):
        return self.s3_resource

    def get_s3_client(self):
        return self.s3_client

    def check_file_exist(self, s3_path: str) -> bool:
        """
        :param s3_path: Target store path for s3.
        :return:
        """

        s3_path_obj = s3_split_path(s3_path)
        try:
            self.s3_resource.Object(s3_path_obj["bucket"], s3_path_obj["store_path"]).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                # The object does not exist.
                return False
            else:
                # Something else has gone wrong.
                raise Exception("Check s3 file exist unknown error...")
        else:
            # The object does exist.
            return True

    def copy_file(self, source_path: str, target_path: str):
        """
        :param source_path: Source s3 path location
        :param target_path: Target s3 path location
        :return:
        """
        source_path_obj = s3_split_path(source_path)
        target_path_obj = s3_split_path(target_path)

        self.s3_resource.Object(target_path_obj["bucket"], target_path_obj["store_path"]).copy_from(
            CopySource=source_path_obj["bucket"] + '/' + source_path_obj["store_path"],
        )

    def delete_file(self, s3_path: str):
        """
        :param s3_path: Target store path for s3.
        :return:
        """
        s3_path_obj = s3_split_path(s3_path)
        self.s3_resource.Object(s3_path_obj["bucket"], s3_path_obj["store_path"]).delete()

    def download_file(self, s3_path: str, local_path: str, filename: str):
        """
        :param s3_path: Target store path for s3.
        :param local_path: Local path
        :param filename: File name
        :return:
        """
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        s3_path_obj = s3_split_path(s3_path)
        self.s3_resource.Bucket(s3_path_obj["bucket"]).download_file(s3_path_obj["store_path"], os.path.join(local_path, filename))

    def upload_by_local_path(self, s3_path: str, local_path: str, text_with_utf8: bool = True):
        """
        :param s3_path: Target store path for s3.
        :param local_path: Local file path.
        :param text_with_utf8: If content-type start with "text/" then put ;charset=utf-8 after.
        :return:
        """
        if not os.path.exists(local_path):
            raise Exception("Local file doesn't exist!")

        content_type = get_content_type_4_filename(s3_path, text_with_utf8)
        s3_path_obj = s3_split_path(s3_path)

        self.s3_client.upload_file(local_path,
                                   s3_path_obj["bucket"],
                                   s3_path_obj["store_path"],
                                   ExtraArgs={'ContentType': content_type})

    def upload_file(self, s3_path: str, content: bytes, metadata: Optional[dict] = None, text_with_utf8: bool = True):
        """
        :param s3_path: Target store path for s3.
        :param content: The content of file, if text-like use content.encode("utf-8"), if binary then put directly.
        :param metadata: Custom metadata for file.
        :param text_with_utf8: If content-type start with "text/" then put ;charset=utf-8 after.
        :return:
        """
        s3_path_obj = s3_split_path(s3_path)
        content_type = get_content_type_4_filename(s3_path, text_with_utf8)

        object_put = self.s3_resource.Object(s3_path_obj["bucket"], s3_path_obj["store_path"])
        if metadata:
            object_put.put(Body=content, ContentType=content_type, Metadata=metadata)
        else:
            object_put.put(Body=content, ContentType=content_type)

    def get_file_meta_info(self, s3_path: str) -> dict:
        """
        :param s3_path: Target store path for s3.
        :return:
        """
        s3_path_obj = s3_split_path(s3_path)
        response = self.s3_client.head_object(Bucket=s3_path_obj["bucket"], Key=s3_path_obj["store_path"])
        return {
            "content_type": response['ContentType'],
            "metadata": response['Metadata'],
        }

    def read_text_like_file(self, s3_path: str, decoding: str = "utf-8") -> str:
        """
        :param s3_path: Target store path for s3.
        :param decoding: decoding, default is "utf-8".
        :return:
        """
        s3_path_obj = s3_split_path(s3_path)
        obj = self.s3_client.get_object(Bucket=s3_path_obj["bucket"], Key=s3_path_obj["store_path"])
        return obj['Body'].read().decode(decoding)


class AwsS3WrapperAsync:
    """Encapsulates Amazon S3 async actions for Orbitfin using aioboto3"""

    def __init__(self, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None):
        """
        初始化异步 S3 包装器
        
        :param aws_access_key_id: AWS access key ID（可选，不提供则使用 AWS CLI 配置或环境变量）
        :param aws_secret_access_key: AWS secret access key（可选）
        
        凭证获取顺序：
        1. 直接传入的参数
        2. 环境变量（AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY）
        3. AWS CLI 配置文件（~/.aws/credentials）
        4. IAM 角色（如果在 EC2/ECS 上运行）
        """
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        # 如果提供了凭证，使用指定凭证；否则使用默认凭证链
        if aws_access_key_id and aws_secret_access_key:
            self.session = aioboto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        else:
            # 使用默认凭证链（环境变量、AWS CLI 配置、IAM 角色等）
            self.session = aioboto3.Session()

    @classmethod
    def from_s3(cls, *args, **kwargs):
        """
        创建 AwsS3WrapperAsync 实例
        
        支持从以下来源获取 AWS 凭证（按优先级）：
        1. kwargs 参数（aws_access_key_id, aws_secret_access_key）
        2. 环境变量（AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY）
        3. AWS CLI 配置文件（~/.aws/credentials）
        4. IAM 角色
        
        示例：
            # 使用默认凭证链（推荐）
            wrapper = AwsS3WrapperAsync.from_s3()
            
            # 显式指定凭证
            wrapper = AwsS3WrapperAsync.from_s3(
                aws_access_key_id="xxx",
                aws_secret_access_key="yyy"
            )
        """
        # 尝试从 kwargs 或环境变量获取凭证（可选）
        aws_access_key_id = kwargs.get("aws_access_key_id") or os.environ.get("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = kwargs.get("aws_secret_access_key") or os.environ.get("AWS_SECRET_ACCESS_KEY")
        
        return cls(aws_access_key_id, aws_secret_access_key)

    async def check_file_exist(self, s3_path: str) -> bool:
        """
        检查 S3 文件是否存在
        :param s3_path: S3 路径
        :return: 文件是否存在
        """
        s3_path_obj = s3_split_path(s3_path)
        
        async with self.session.client('s3') as s3_client:
            try:
                await s3_client.head_object(
                    Bucket=s3_path_obj["bucket"],
                    Key=s3_path_obj["store_path"]
                )
                return True
            except ClientError as e:
                if e.response['Error']['Code'] == "404":
                    return False
                else:
                    raise Exception("Check s3 file exist unknown error...")

    async def copy_file(self, source_path: str, target_path: str):
        """
        复制 S3 文件
        :param source_path: 源 S3 路径
        :param target_path: 目标 S3 路径
        """
        source_path_obj = s3_split_path(source_path)
        target_path_obj = s3_split_path(target_path)

        async with self.session.client('s3') as s3_client:
            copy_source = {
                'Bucket': source_path_obj["bucket"],
                'Key': source_path_obj["store_path"]
            }
            await s3_client.copy_object(
                CopySource=copy_source,
                Bucket=target_path_obj["bucket"],
                Key=target_path_obj["store_path"]
            )

    async def delete_file(self, s3_path: str):
        """
        删除 S3 文件
        :param s3_path: S3 路径
        """
        s3_path_obj = s3_split_path(s3_path)
        
        async with self.session.client('s3') as s3_client:
            await s3_client.delete_object(
                Bucket=s3_path_obj["bucket"],
                Key=s3_path_obj["store_path"]
            )

    async def download_file(self, s3_path: str, local_path: str, filename: str):
        """
        从 S3 下载文件到本地
        :param s3_path: S3 路径
        :param local_path: 本地目录路径
        :param filename: 文件名
        """
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        s3_path_obj = s3_split_path(s3_path)
        local_file_path = os.path.join(local_path, filename)

        async with self.session.client('s3') as s3_client:
            response = await s3_client.get_object(
                Bucket=s3_path_obj["bucket"],
                Key=s3_path_obj["store_path"]
            )
            async with aiofiles.open(local_file_path, 'wb') as f:
                await f.write(await response['Body'].read())

    async def upload_by_local_path(self, s3_path: str, local_path: str, text_with_utf8: bool = True):
        """
        从本地路径上传文件到 S3
        :param s3_path: S3 目标路径
        :param local_path: 本地文件路径
        :param text_with_utf8: 如果是文本文件，是否添加 utf-8 编码标识
        """
        if not os.path.exists(local_path):
            raise Exception("Local file doesn't exist!")

        content_type = get_content_type_4_filename(s3_path, text_with_utf8)
        s3_path_obj = s3_split_path(s3_path)

        async with self.session.client('s3') as s3_client:
            async with aiofiles.open(local_path, 'rb') as f:
                content = await f.read()
                await s3_client.put_object(
                    Bucket=s3_path_obj["bucket"],
                    Key=s3_path_obj["store_path"],
                    Body=content,
                    ContentType=content_type
                )

    async def upload_file(self, s3_path: str, content: bytes, metadata: Optional[dict] = None, text_with_utf8: bool = True):
        """
        上传文件内容到 S3
        :param s3_path: S3 目标路径
        :param content: 文件内容（字节）
        :param metadata: 自定义元数据
        :param text_with_utf8: 如果是文本文件，是否添加 utf-8 编码标识
        """
        s3_path_obj = s3_split_path(s3_path)
        content_type = get_content_type_4_filename(s3_path, text_with_utf8)

        async with self.session.client('s3') as s3_client:
            put_args = {
                'Bucket': s3_path_obj["bucket"],
                'Key': s3_path_obj["store_path"],
                'Body': content,
                'ContentType': content_type
            }
            if metadata:
                put_args['Metadata'] = metadata
            
            await s3_client.put_object(**put_args)

    async def get_file_meta_info(self, s3_path: str) -> dict:
        """
        获取 S3 文件的元信息
        :param s3_path: S3 路径
        :return: 包含 content_type 和 metadata 的字典
        """
        s3_path_obj = s3_split_path(s3_path)
        
        async with self.session.client('s3') as s3_client:
            response = await s3_client.head_object(
                Bucket=s3_path_obj["bucket"],
                Key=s3_path_obj["store_path"]
            )
            return {
                "content_type": response['ContentType'],
                "metadata": response['Metadata'],
            }

    async def read_text_like_file(self, s3_path: str, decoding: str = "utf-8") -> str:
        """
        读取 S3 文本文件内容
        :param s3_path: S3 路径
        :param decoding: 解码方式，默认 utf-8
        :return: 文件文本内容
        """
        s3_path_obj = s3_split_path(s3_path)
        
        async with self.session.client('s3') as s3_client:
            response = await s3_client.get_object(
                Bucket=s3_path_obj["bucket"],
                Key=s3_path_obj["store_path"]
            )
            content = await response['Body'].read()
            return content.decode(decoding)
