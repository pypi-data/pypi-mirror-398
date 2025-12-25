import os
import datetime
from collections import defaultdict
from importlib.metadata import version
import googletrans


class DocumentProcessor:
    if version("googletrans") < "4.0.2":
        raise ImportError(f"googletrans >= 4.0.2 is required for async support. {version('googletrans')}")
    AUDIO_SUFFIXES = [".mp3", ".wav", ".aac", ".wma", ".m4a"]
    VIDEO_SUFFIXES = [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".3gp", ".hevc"]
    PDF_SUFFIXES = [".pdf"]
    DOC_SUFFIXES = [".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"]
    TXT_SUFFIXES = [".txt", ".html", ".htm", ".xhtml"]
    ALL_ALLOWED_SUFFIXES = set(AUDIO_SUFFIXES + VIDEO_SUFFIXES + PDF_SUFFIXES + DOC_SUFFIXES + TXT_SUFFIXES)

    DATA_PROCESS_STEPS = ['convert', 'extract', 'embedding', 'success']

    @staticmethod
    def get_file_suffix(file_path):
        return f".{file_path.split('.')[-1]}".lower()

    @staticmethod
    async def translate_text(text, dest='en'):
        """异步翻译函数 https://pypi.org/project/googletrans/"""
        translator = googletrans.Translator()
        result = await translator.translate(text, dest=dest)
        return result.text

    @staticmethod
    def create_xbrl_template():
        return {
            "_id": "",
            "source_type": "",
            "x_attachments": [],
            "status": "init",
            "logs": [],
            "metadata": {},
            "x_created_date": datetime.datetime.now(),
            "x_updated_date": datetime.datetime.now(),
        }

    @classmethod
    def stock_us_filter_by_is_primary(cls, doc):
        if not doc:
            return None
        if doc.get('x_spider_name') != 'stock_us':
            return doc
        doc['x_attachments'] = [att for att in doc.get('x_attachments', []) if 'is_primary' in att]
        if len(doc['x_attachments']) == 0:
            return None
        return doc

    @classmethod
    def stock_indiabse_filter_by_prefix(cls, doc):
        if not doc:
            return None
        if doc.get('x_spider_name') != 'stock_indiabse':
            return doc
        doc['x_attachments'] = [att for att in doc.get('x_attachments', []) if att['file_type'].lower() != '.xml']
        if len(doc['x_attachments']) == 0:
            return None
        return doc

    @classmethod
    def file_type_filter(cls, doc):
        if not doc:
            return None
        suffixes = {cls.get_file_suffix(att['store_path']) for att in doc.get('x_attachments', [])}
        return doc if suffixes.issubset(cls.ALL_ALLOWED_SUFFIXES) else None

    @classmethod
    def xbrl_type_check(cls, doc):
        is_xbrl = doc.get('x_info_data', {}).get('is_xbrl') == 'true'
        x_attachments = doc.get('x_attachments', [])
        convert_status = doc.get('x_status_list', {}).get('status_convert', {}).get('status')
        xhtml_count = sum(1 for att in x_attachments if att['store_path'].lower().endswith('.xhtml'))

        if is_xbrl or xhtml_count > 0 and convert_status != 'convert_done':
            template = cls.create_xbrl_template()
            template['_id'] = doc['_id']
            template['source_type'] = doc.get('x_report_source', {}).get('source_type', '')
            template['x_attachments'] = [{
                "file_hash": att['file_hash'],
                "store_path": f"s3://{att['bucket']}/{att['store_path']}",
                "store_path_converted_pdf": "",
                "store_path_converted_pdf_image": "",
            } for att in x_attachments]
            return True, template

        return False, None

    @staticmethod
    def get_start_stage_target_stage(doc, custom_process_step_list):
        status_info = doc.get('x_status_list', {}).get('status_convert', {})
        status = status_info.get('status')
        status_txt = status_info.get('status_txt')
        x_spider_name = doc['x_spider_name']

        if custom_process_step_list:
            return custom_process_step_list[0], custom_process_step_list[1], x_spider_name

        if status != 'convert_done':
            return 'convert', 'embedding', x_spider_name

        if status_txt not in ['convert_txt_done', 'convert_txt_embedding']:
            return 'extract', 'embedding', x_spider_name

        if status_txt == 'convert_txt_done':
            return 'embedding', 'embedding', x_spider_name

        return 'success', 'success', x_spider_name

    @staticmethod
    def update_target_stage_by_report_type(doc, target_stage):
        report_type_ids = doc.get('x_orbit_data', {}).get('report_type_id_list', [])
        return "extract" if report_type_ids == ['19999'] else target_stage

    @staticmethod
    def update_target_stage_by_reported_at(doc, target_stage):
        date_str = doc.get('x_reported_at_utc_date', '1970-01-01')
        try:
            reported_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            reported_date = datetime.datetime(1970, 1, 1)
        return "extract" if reported_date < datetime.datetime(2023, 1, 1) else target_stage

    @classmethod
    async def create_record(cls, doc, start_stage, important_level):
        attachments = doc.get('x_attachments', []) if start_stage == 'convert' else doc.get('x_attachments_pdf', [])
        s3_path_info = []
        add_extends = {}
        for att in attachments:
            if len(att['file_name']) > 2000 or len(att['file_name'].encode('utf-8')) > 2000:
                return False, None

            if start_stage == 'convert' and not add_extends:
                _, ext = os.path.splitext(att['store_path'])
                if ext in cls.AUDIO_SUFFIXES or ext in cls.VIDEO_SUFFIXES:
                    add_extends = {
                        "original_title": doc['x_orbit_data']['report_title'],
                        "title": await cls.translate_text(text=doc['x_orbit_data']['report_title']),
                        "published": doc['x_reported_at_utc_date'],
                        "tickers": [],
                        "perm_id_list": doc['x_orbit_data']['perm_id_list'],
                        "report_type_id_list_str": doc['x_orbit_data']['report_type_id_list']
                    }

            s3_path_info.append({
                'store_path': f"s3://{att['bucket']}/{att['store_path']}" if start_stage == 'convert' else att[
                    'store_path'],
                'file_name': att['file_name']
            })
        result_dict = {'id': doc['_id'], 's3_path_info': s3_path_info, 'important_level': important_level}
        if add_extends:
            result_dict['extends'] = add_extends
        return True, result_dict

    @staticmethod
    def create_result_info(process_type, message, result_data):
        return {
            'process_type': process_type,
            'message': message,
            'result_data': result_data
        }

    @classmethod
    async def process(cls, doc, custom_process_step, important_level):
        report_id = doc['_id']
        # 筛选文件
        doc = cls.stock_us_filter_by_is_primary(doc)
        doc = cls.stock_indiabse_filter_by_prefix(doc)
        # 校验文件类型必须在筛选文件类型之后
        doc = cls.file_type_filter(doc)
        if doc is None:
            return cls.create_result_info("error", "Document file type is not allowed.", report_id)

        is_xbrl, xbrl_data = cls.xbrl_type_check(doc)
        if is_xbrl:
            return cls.create_result_info("xbrl", "XBRL or Xhtml format cannot be processed.", xbrl_data)

        start_stage, target_stage, x_spider_name = cls.get_start_stage_target_stage(doc, custom_process_step)

        # 判断 特殊条件下的数据不做embedding ('19999'类型和报告日期小于2020-01-01)
        if target_stage == 'embedding' and not custom_process_step:
            target_stage = cls.update_target_stage_by_report_type(doc, target_stage)
            target_stage = cls.update_target_stage_by_reported_at(doc, target_stage)
            # 特殊情况下只需要做embedding 但是这个数据被条件限制为只做到提取时状态异常
            if start_stage == 'embedding' and target_stage == 'extract':
                start_stage = 'success'
                target_stage = 'success'

        if cls.DATA_PROCESS_STEPS.index(target_stage) < cls.DATA_PROCESS_STEPS.index(start_stage):
            return cls.create_result_info("step_error",
                                          "Invalid process sequence: 'start_stage' occurs before 'target_stage'.",
                                          report_id)

        file_name_check_status, record = await cls.create_record(doc, start_stage, important_level)
        if not file_name_check_status:
            return cls.create_result_info("error", "Document file name too lang.", report_id)

        return cls.create_result_info("file_flow", "Success", [start_stage, target_stage, x_spider_name, record])

    @classmethod
    def split_data_by_spider_name_and_step(cls, process_records):
        file_flow_info = defaultdict(list)
        xbrl_data_list = []
        except_id_list = []
        doc_error_list = []

        for item in process_records:
            process_type = item.get('process_type')
            if process_type == 'xbrl':
                xbrl_data_list.append(item['result_data'])
            elif process_type == 'file_flow':
                start_stage, target_stage, x_spider_name, record = item['result_data']
                key = f"{start_stage}@__@{target_stage}@__@{x_spider_name}"
                file_flow_info[key].append(record)
            elif process_type == 'step_error':
                except_id_list.append(item['result_data'])
            elif process_type == 'error':
                doc_error_list.append(item['result_data'])
            else:
                raise KeyError(
                    f"Unknown process_type: {process_type}. Expected one of ['xbrl', 'file_flow', 'step_error', 'error'].")

        return file_flow_info, xbrl_data_list, except_id_list, doc_error_list
