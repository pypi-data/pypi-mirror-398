from typing import Optional, List, Dict, Any, Coroutine
from pathlib import Path
import boto3
import json
import tempfile
import datetime
import time
import pytz
import logging
import requests
from orbitkit import id_srv
from orbitkit.util import s3_split_path, S3Util, get_from_dict_or_env, ExtenCons, s3_path_join, \
    get_content_type_4_filename
from typing import Optional
import urllib3
import fitz  # PyMuPDF
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class SplitPageOptions:
    def __init__(self, split_page_number: int = 20, split_size: float = 1 * 1024 * 1024,
                 split_threshold: float = 5 * 1024 * 1024):
        self.split_page_number = split_page_number
        self.split_size = split_size
        self.split_threshold = split_threshold

    def __repr__(self):
        return (f"SplitPageOptions(split_page_number={self.split_page_number}, "
                f"split_size={self.split_size}, "
                f"split_threshold={self.split_threshold})")

    def needs_split(self, file_size: float) -> bool:
        return file_size > self.split_threshold


class PdfExtractorNetmindFileAnalysis:
    def __init__(self, s3_path: str,
                 max_workers: int = 4,
                 slice_option: Optional[SplitPageOptions] = SplitPageOptions(), **kwargs):
        self.bucket_tmp = os.getenv('BUCKET_TMP', 'orbit-tmp')
        self.bucket_tmp_group = os.getenv('BUCKET_TMP_GROUP', 'fileflow/')
        self.s3_path = s3_path
        self.slice_option = slice_option
        self.max_workers = max_workers
        self.input_file_size = None
        self.total_pages = None
        self.aws_access_key_id = get_from_dict_or_env(kwargs, "aws_access_key_id", "AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = get_from_dict_or_env(kwargs, "aws_secret_access_key", "AWS_SECRET_ACCESS_KEY")
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=self.aws_access_key_id,
                                      aws_secret_access_key=self.aws_secret_access_key)
        self.s3_resource = boto3.resource('s3',
                                          aws_access_key_id=self.aws_access_key_id,
                                          aws_secret_access_key=self.aws_secret_access_key)

    def upload_file_to_s3(self, local_key: str, remote_key: str):
        _remote_key = f'{self.bucket_tmp_group}{remote_key}'
        self.s3_resource.Object(self.bucket_tmp, _remote_key).upload_file(local_key)
        logger.info(f"File {local_key} uploaded to s3://{self.bucket_tmp}/{_remote_key}")

    def download_file_from_s3(self, bucket: str, remote_key: str, local_key: str):
        self.s3_resource.Bucket(bucket).download_file(remote_key, local_key)
        logger.info(f"File s3://{bucket}/{remote_key} downloaded to {local_key}")

    def split_pdf(self, input_file: str, output_folder: str) -> List[Dict[str, str]]:
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        hash_id = id_srv.get_random_short_id()
        # 获取输入文件的大小
        input_file_path = Path(input_file)
        self.input_file_size = input_file_path.stat().st_size  # 获取输入文件的大小（字节）
        pdf_document = fitz.open(input_file)
        total_pages = len(pdf_document)
        self.total_pages = total_pages
        pages_per_split = self.slice_option.split_page_number
        file_path_list = []

        for start_page in range(0, total_pages, pages_per_split):
            pdf_writer = fitz.open()
            end_page = min(start_page + pages_per_split - 1, total_pages - 1)
            pdf_writer.insert_pdf(pdf_document, from_page=start_page, to_page=end_page)
            remote_name = f'{hash_id}_{start_page // pages_per_split + 1}.pdf'
            output_file = Path(output_folder) / remote_name
            pdf_writer.save(str(output_file))
            pdf_writer.close()
            file_path_list.append({'local_path': str(output_file), "remote_name": remote_name})

        pdf_document.close()
        return file_path_list

    def extract(self) -> list[str]:
        s3_path_obj = s3_split_path(self.s3_path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            split_folder = Path(tmp_dir) / 'split'
            file_name = s3_path_obj['store_path'].split('/')[-1]
            file_path = Path(tmp_dir) / file_name

            self.download_file_from_s3(s3_path_obj['bucket'], s3_path_obj['store_path'], str(file_path))
            logger.info("Downloaded file successfully...")

            file_path_list = self.split_pdf(str(file_path), str(split_folder))
            # for file in file_path_list:
            #     self.upload_file_to_s3(file['local_path'], file['remote_name'])
            # 使用 ThreadPoolExecutor 进行多线程上传
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {executor.submit(self.upload_file_to_s3, file['local_path'], file['remote_name']): file
                                  for file in file_path_list}

                for future in as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        future.result()  # 获取上传结果
                        logger.warning(f"Uploaded {file['remote_name']} successfully.")
                    except Exception as e:
                        logger.error(f"Error uploading {file['remote_name']}: {e}")
                        raise

            return [f's3://{self.bucket_tmp}/{self.bucket_tmp_group}{i["remote_name"]}' for i in file_path_list]


class PdfExtractorNetmindExtract:
    def __init__(self, s3_path: str, parse_timeout: int = 10 * 60 + 3, **kwargs):
        self.s3_path = s3_path
        self.aws_access_key_id = get_from_dict_or_env(kwargs, "aws_access_key_id", "AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = get_from_dict_or_env(kwargs, "aws_secret_access_key", "AWS_SECRET_ACCESS_KEY")
        self.parse_timeout = parse_timeout
        netmind_token = get_from_dict_or_env(
            kwargs, "netmind_token", "NETMIND_TOKEN",
        )
        netmind_service_id = get_from_dict_or_env(
            kwargs, "netmind_service_id", "NETMIND_SERVICE_ID",
        )
        self.netmind_token = netmind_token
        self.netmind_endpoint = f'https://api.netmind.ai/inference-api/v1/inference_service/{netmind_service_id}/api/v1/parse-pdf'
        self.header = {"Authorization": f"Bearer {self.netmind_token}"}
        self.s3_client = boto3.client('s3',
                                      aws_access_key_id=self.aws_access_key_id,
                                      aws_secret_access_key=self.aws_secret_access_key)
        self.s3_resource = boto3.resource('s3',
                                          aws_access_key_id=self.aws_access_key_id,
                                          aws_secret_access_key=self.aws_secret_access_key)

    def netmind_api(self):
        s3_path_obj = s3_split_path(self.s3_path)
        presigned_url = self._generate_presigned_url(s3_path_obj)
        logger.warning("Get presigned_url successfully...")
        api_response_time, json_response = self.get_netmind_response(presigned_url)
        return api_response_time, self._save_json_to_s3(json_response, s3_path_obj)

    def _generate_presigned_url(self, s3_path_obj):
        return self.s3_client.generate_presigned_url('get_object',
                                                     Params={
                                                         'Bucket': s3_path_obj["bucket"],
                                                         'Key': s3_path_obj["store_path"]
                                                     },
                                                     ExpiresIn=604800)

    def get_netmind_response(self, presigned_url):
        start = time.time()
        files = {"url": (None, presigned_url)}
        response = requests.post(
            self.netmind_endpoint, files=files, timeout=self.parse_timeout, headers=self.header,
        )
        # 状态检查
        response.raise_for_status()
        api_response_time = time.time() - start
        logger.info(f"Extract text by using Netmind successfully: {api_response_time}")
        return api_response_time, response.json()

    def _save_json_to_s3(self, json_data, s3_path_obj):
        json_key = f"{s3_path_obj['store_path']}.json"  # 生成 JSON 文件名
        local_name = json_key.split('/')[-1]
        json_content = json.dumps(json_data)  # 转换为 JSON 字符串
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_folder = os.path.join(tmp_dir, 'input')
            if not os.path.exists(input_folder):
                os.makedirs(input_folder)
            local_key = os.path.join(input_folder, local_name)  # 临时文件路径
            # 将 JSON 数据写入临时文件
            with open(local_key, 'w') as json_file:
                json_file.write(json_content)
            # 上传到 S3
            self.upload_file_to_s3(s3_path_obj['bucket'], local_key, json_key)
        return f"s3://{s3_path_obj['bucket']}/{json_key}"

    def upload_file_to_s3(self, bucket, local_key: str, remote_key: str):
        self.s3_resource.Object(bucket, remote_key).upload_file(local_key)
        logger.warning(f"File {local_key} Uploaded To s3://{bucket}/{remote_key}")


class PdfExtractorNetmindMerge:
    def __init__(self,
                 source_s3_path: str = None,
                 temp_folder: Optional[str] = None,
                 s3_util: Optional[S3Util] = None,
                 txt_vector: str = 'txt-vector',
                 is_page_number_discontinuity_exception_thrown: bool = False, #页码不连续异常抛出
                 slice_option: Optional[SplitPageOptions] = SplitPageOptions(),
                 **kwargs):
        self.aws_access_key_id = get_from_dict_or_env(kwargs, "aws_access_key_id", "AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = get_from_dict_or_env(kwargs, "aws_secret_access_key", "AWS_SECRET_ACCESS_KEY")
        self.temp_folder = temp_folder
        self.txt_vector = txt_vector
        self.slice_option = slice_option
        self.source_s3_path = source_s3_path
        self.is_page_number_discontinuity_exception_thrown = is_page_number_discontinuity_exception_thrown
        if not source_s3_path:
            raise Exception('not params source source_s3_path')
        if s3_util:
            self.s3_util = s3_util
        else:
            # Try to get key aws pair
            aws_access_key_id = get_from_dict_or_env(
                kwargs, "aws_access_key_id", "AWS_ACCESS_KEY_ID",
            )

            aws_secret_access_key = get_from_dict_or_env(
                kwargs, "aws_secret_access_key", "AWS_SECRET_ACCESS_KEY",
            )
            self.s3_util = S3Util(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        self._s3_resource = self.s3_util.get_s3_resource()
        self._s3_client = self.s3_util.get_s3_client()

    def upload_file_to_s3(self, bucket, local_key: str, remote_key: str):
        self._s3_resource.Object(bucket, remote_key).upload_file(local_key)
        logger.warning(f"File {local_key} Uploaded To s3://{bucket}/{remote_key}")

    def download_file_from_s3(self, bucket: str, remote_key: str, local_key: str):
        self._s3_resource.Bucket(bucket).download_file(remote_key, local_key)
        logger.info(f"File s3://{bucket}/{remote_key} downloaded to {local_key}")

    def megre_json(self, json_s3_path_list):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # page 字典
            meta_data = {}
            for _s3_path in json_s3_path_list:
                if '.json' not in _s3_path:
                    raise Exception('s3 file path type error')
                obj = s3_split_path(_s3_path)
                local_path = os.path.join(tmp_dir, obj['store_path'].split('/')[-1])
                self.download_file_from_s3(obj['bucket'], obj['store_path'], local_path)
                # 下载s3文件，读取json
                with open(local_path, 'r') as file:
                    _split_response_json = json.load(file)
                file_item_name = _s3_path.split('/')[-1].replace('.json', '')
                start_page = (int(
                    file_item_name.split('_')[-1].split('.')[0]) - 1) * self.slice_option.split_page_number
                meta_data[start_page] = _split_response_json
            logger.warning("[JSON] Down json result successfully...")
            # 合并
            file_arr = []
            for key, value in meta_data.items():
                logger.info(f"{key} merge {'+' * 3}")
                # 更改page
                change_page_data = [{**item, 'page': item['page'] + int(key)} for item in value]
                file_arr.extend(change_page_data)
            # 根据 page 和 seq_no 排序
            sorted_file_arr = sorted(file_arr, key=lambda x: (x['page'], x['seq_no']))
            # 检查页码连续性
            if sorted_file_arr:
                # 收集所有页码并去重排序
                all_pages = sorted(set(item['page'] for item in sorted_file_arr))

                # 检查页码是否连续
                for i in range(1, len(all_pages)):
                    if all_pages[i] != all_pages[i - 1] + 1:
                        missing_pages = list(range(all_pages[i - 1] + 1, all_pages[i]))
                        if self.is_page_number_discontinuity_exception_thrown:
                            raise ValueError(
                                f"页码不连续错误！在 {all_pages[i - 1]} 页之后直接出现了 {all_pages[i]} 页，"
                                f"缺少页码: {missing_pages}"
                            )
                        else:
                            print(f"页码不连续错误！在 {all_pages[i - 1]} 页之后直接出现了 {all_pages[i]} 页，缺少页码: {missing_pages}")
            logger.info("[JSON] Merge json result successfully...")
            return sorted_file_arr

    def extract(self, json_s3_path_list):
        response_json = self.megre_json(json_s3_path_list)
        if self.temp_folder:
            if not os.path.exists(self.temp_folder):
                raise Exception('The temp folder given not exists...')
            self.extract_detail(self.temp_folder, response_json)
        else:
            with tempfile.TemporaryDirectory() as tmp_dir:
                input_folder = os.path.join(tmp_dir, 'input')
                if not os.path.exists(input_folder):
                    os.makedirs(input_folder)

                self.extract_detail(input_folder, response_json)

    def extract_detail(self, input_folder, response_json):
        s3_path_obj = s3_split_path(self.source_s3_path)
        # 禁用 InsecureRequestWarning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # >>>>>>>>>>>>>>>>>> Start to generate pages/blocks/raw
        netmind_reg_file = os.path.join(input_folder, f'netmind_reg.txt')
        blocks_file = os.path.join(input_folder, f'blocks.txt')
        pages_file = os.path.join(input_folder, f'pages.txt')

        with open(netmind_reg_file, "w+", encoding='utf-8') as f_reg, \
                open(blocks_file, "w+", encoding='utf-8') as f_blocks, \
                open(pages_file, "w+", encoding='utf-8') as f_pages:

            current_page_num = 0
            current_page_txt = ""
            all_local_image_path = []
            for ind, block in enumerate(response_json, start=1):
                # 如果是图片类型，则进行图片的转换
                if block["type"] in ["image"]:
                    for item_img in block["image_detail"]:
                        # res_img = requests.get(item_img["path"], verify=False)
                        # if res_img.status_code != 200:
                        #     raise Exception(f"Download image failed: {res_img.status_code}")

                        # Build image local path for using
                        image_extension = str(item_img["path"]).split(".")[-1]
                        image_local_relitive_path = f"{id_srv.get_random_short_id_v2()}.{image_extension}"
                        # image_local_abs_path = os.path.join(input_folder, image_local_relitive_path)
                        # with open(image_local_abs_path, mode="wb") as img_tmp:
                        #     img_tmp.write(res_img.content)
                        # all_local_image_path.append(image_local_relitive_path)
                        all_local_image_path.append({
                            "path_raw": item_img["path"],
                            "path_s3": f"images/{image_local_relitive_path}",
                        })
                        # 直接修改其 image path 为自己的
                        item_img["path"] = f"images/{image_local_relitive_path}"

                # For raw
                f_reg.write(json.dumps(block, ensure_ascii=False) + "\n")

                # For blocks
                f_blocks.write(json.dumps(self.convert_2_block(block), ensure_ascii=False) + "\n")

                # For page: image Not in combine list
                if block["type"] in ["image"]:
                    continue
                if "sentence" not in block:
                    continue
                if block["page"] != current_page_num:
                    if current_page_num != 0:
                        # 开辟新的页并且将之前的页写入到文件中
                        f_pages.write(json.dumps({
                            "id": id_srv.get_random_short_id(),
                            "page": current_page_num,
                            "sentence": current_page_txt,
                        }, ensure_ascii=False) + "\n")

                    # 重置为下一页做准备
                    current_page_num = block["page"]
                    current_page_txt = block["sentence"] + "\n\n"
                else:
                    # 说明在同一页
                    current_page_txt += block["sentence"] + "\n\n"

                # 最后一页的话，最后加入
                if ind == len(response_json):
                    f_pages.write(json.dumps({
                        "id": id_srv.get_random_short_id(),
                        "page": current_page_num,
                        "sentence": current_page_txt,
                    }, ensure_ascii=False) + "\n")

        logger.info(f"Write [blocks.txt] and [pages.txt] successfully...")

        # 上传各种文件到 s3 ---------------------------------------------------------------------------------------
        # Update images to s3
        for item_img in tqdm(all_local_image_path):
            with requests.get(item_img["path_raw"], stream=True) as response:
                response.raise_for_status()  # 检查是否成功
                self._s3_client.upload_fileobj(
                    response.raw,
                    s3_path_obj['bucket'],
                    s3_path_join(self.txt_vector, s3_path_obj['store_path'], item_img["path_s3"]),
                    ExtraArgs={'ContentType': get_content_type_4_filename(item_img["path_raw"])},
                )

            # for item_img in all_local_image_path:
            #     self._s3_client.upload_file(
            #         os.path.join(input_folder, item_img),
            #         s3_path_obj['bucket'], s3_path_join(self.txt_vector, s3_path_obj['store_path'], 'images', item_img),
            #         ExtraArgs={'ContentType': get_content_type_4_filename(item_img)}
            #     )
        logger.warning("[image] Store images result successfully...")

        # Upload raw files to s3
        self._s3_client.upload_file(
            netmind_reg_file,
            s3_path_obj['bucket'], s3_path_join(self.txt_vector, s3_path_obj['store_path'], f'netmind_reg.txt'),
            ExtraArgs={'ContentType': ExtenCons.EXTEN_TEXT_TXT_UTF8.value}
        )
        logger.info("[raw] Store raw result successfully...")

        # Upload pages files to s3
        pages_txt_key = s3_path_join(self.txt_vector, s3_path_obj['store_path'], f'pages.txt')
        self._s3_client.upload_file(os.path.join(input_folder, 'pages.txt'), s3_path_obj['bucket'], pages_txt_key,
                                    ExtraArgs={'ContentType': ExtenCons.EXTEN_TEXT_TXT_UTF8.value})
        if self.s3_util.check_file_exist(s3_path_obj["bucket"], pages_txt_key) is False:
            raise Exception("[page] Store page result failed...")
        logger.info("[page] Store page result successfully...")

        # Upload blocks files to s3
        blocks_txt_key = s3_path_join(self.txt_vector, s3_path_obj['store_path'], f'blocks.txt')
        self._s3_client.upload_file(os.path.join(input_folder, f'blocks.txt'), s3_path_obj['bucket'], blocks_txt_key,
                                    ExtraArgs={'ContentType': ExtenCons.EXTEN_TEXT_TXT_UTF8.value})
        if self.s3_util.check_file_exist(s3_path_obj["bucket"], blocks_txt_key) is False:
            raise Exception("[block] Store block result failed...")
        logger.info("[block] Store block result successfully...")

        extract_meta = {
            "extraction": {
                "version": "netmind",
                "sub_version": "v1",
                "finished_time": datetime.datetime.now(tz=pytz.timezone('UTC')).strftime('%Y-%m-%dT%H:%M:%S%z')
            },
            "metadata": {},
            "others": {}
        }

        object_put = self._s3_resource.Object(s3_path_obj['bucket'],
                                              s3_path_join(self.txt_vector, s3_path_obj['store_path'],
                                                           f'metadata.txt'))
        object_put.put(Body=json.dumps(extract_meta, ensure_ascii=False),
                       ContentType=ExtenCons.EXTEN_TEXT_TXT_UTF8.value)
        logger.info("[meta] Store extract meta info successfully...")

    def convert_2_block(self, block_raw):
        f_block = {
            "id": block_raw["id"],
            "page": block_raw["page"],
            "seq_no": block_raw["seq_no"],
            "sentence": "",
            "type": block_raw["type"],
            "image_detail": [],
            "text_location": {"location": block_raw["text_location"]["location"]},
        }
        if "sentence" in block_raw:
            f_block["sentence"] = block_raw["sentence"]

        if block_raw["type"] == "image":
            f_block["image_detail"] = block_raw["image_detail"]
        return f_block
