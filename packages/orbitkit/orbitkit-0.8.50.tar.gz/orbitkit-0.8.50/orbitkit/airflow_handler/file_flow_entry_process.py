import os
from collections import Counter
from datetime import datetime
from typing import Optional
import logging
import pymongo
import pytz
import boto3
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from orbitkit.airflow_handler.file_handler_v2 import FileFlowHandleV2
from orbitkit.airflow_handler.data_preprocessing import DocumentProcessor
from orbitkit.orbit_type import OrbitTypeMatcher

logger = logging.getLogger(__name__)


class FilingOfficialProcessor:

    def __init__(self, mongo_uri=None, postgres_uri=None, aws_access_key_id=None, aws_secret_access_key=None, pi2_postgres_uri=None, pi2_database_name=None, databases_fileflow=None):
        mongo_uri = os.environ.get('MONGO_URI_MAIN_USER_APP') if not mongo_uri else mongo_uri
        if not mongo_uri:
            raise KeyError('mongo_uri not set.')

        if not aws_secret_access_key or not aws_access_key_id:
            raise KeyError('aws_access_key_id and aws_secret_access_key not set.')

        self.mongo_client = pymongo.MongoClient(mongo_uri)
        self.data_xbrl_convert_collection = self.mongo_client['filing_reports']['data_xbrl_convert']

        postgres_uri = os.environ.get('PG_URI_AIRFLOW12_USER_NEWSFEEDSITE') if not postgres_uri else postgres_uri
        if not postgres_uri:
            raise KeyError('postgres_uri not set.')
        databases_fileflow = databases_fileflow or "process_net"
        self.file_handler = FileFlowHandleV2(postgres_uri=postgres_uri, database_name=databases_fileflow)
        self.data_processor = DocumentProcessor()
        self.max_batch_size = 10000
        self.all_stat_count = {'all': 0, 'skip': 0, 'doc_error': 0, 'step_error': 0, 'xbrl': 0, 'file_flow': 0}

        self.s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        self.matcher = OrbitTypeMatcher(self.s3_client)
        self.report_type_id_name_map = {i["lv3_id"]: i["lv3_name"] for i in self.matcher.get_full_type_list()}

        self.pi2_postgres_uri = pi2_postgres_uri or os.environ['PG_URI_CX45_USER_GLAUUIADMIN']
        if not self.pi2_postgres_uri:
            raise KeyError('pie_postgres_uri not set.')
        self.databases = pi2_database_name or 'newsfeedsite'
        self.postgres_engine = create_engine(f"{self.pi2_postgres_uri}/{self.databases}", connect_args={"sslmode": "require"})
        self.postgres_session = sessionmaker(bind=self.postgres_engine)
        self.Session = scoped_session(self.postgres_session)
        self.postgres_metadata = MetaData()

        self.pi2_table = Table(
            'primary_instrument_2_release', self.postgres_metadata,
            autoload_with=self.postgres_engine, schema='security_master'
        )

        self.postgres_engine2 = create_engine(f"{postgres_uri}/{databases_fileflow}",
                                             connect_args={"sslmode": "require"})
        self.postgres_session2 = sessionmaker(bind=self.postgres_engine2)
        self.Session2 = scoped_session(self.postgres_session2)

        self.op_meta = Table(
            'op_meta', self.postgres_metadata,
            autoload_with=self.postgres_engine2, schema='public'
        )

    @contextmanager
    def session_scope(self, use_session=None):
        session = self.Session() if not use_session else use_session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            self.Session.remove()

    def create_spider_name_source_type_map(self, collection, label):

        def find_duplicates(keys):
            return [k for k, v in Counter(keys).items() if v > 1]

        map_dict = {}
        pipeline = [{'$group': {'_id': "$x_spider_name"}}]

        for document in collection.aggregate(pipeline):
            map_dict[document['_id']] = label

        all_keys = list(map_dict.keys())
        duplicates = find_duplicates(all_keys)
        if duplicates:
            raise KeyError(f"Duplicate x_spider_name found: {duplicates}")

        return map_dict

    def send_xbrl_data_to_mongo(self, xbrl_data_list):
        if not xbrl_data_list:
            return
        report_id_list = list(set([i['_id'] for i in xbrl_data_list]))
        result = self.data_xbrl_convert_collection.find({'_id': {'$in': report_id_list}}, {'_id': 1}).batch_size(self.max_batch_size)
        exists_id_list = [i['_id'] for i in result]
        new_xbrl_data_list = [i for i in xbrl_data_list if i['_id'] not in exists_id_list]
        if not new_xbrl_data_list:
            return
        self.data_xbrl_convert_collection.insert_many(new_xbrl_data_list)
        logger.info(f'{len(new_xbrl_data_list)}-xbrl data inserted.')

    def update_doc_status_to_convert(self, collection, report_id_list):
        if len(report_id_list) == 0:
            return
        collection.update_many({
            '_id': {'$in': report_id_list}
        }, {'$set': {
            "x_status_list.status_convert.status": "convert_failed",
            "x_status_list.status_convert.status_txt": "convert_txt_init",
            "x_status_list.status_convert.status_meta": "meta_init",
            "x_updated_date": datetime.now(tz=pytz.timezone('UTC')).strftime("%Y-%m-%dT%H:%M:%S%z"),
        }})
        logger.info(f'Unable to convert {len(report_id_list)} document(s) due to unsupported file type.')

    def update_extends_fields(self, perm_id_list, file_flow_info):
        stmt = select(self.pi2_table.c.orbit_entity_id, self.pi2_table.c.ticker).where(self.pi2_table.c.orbit_entity_id.in_(perm_id_list))
        orbit_entity_id_ticker_map = {}
        with self.session_scope() as session:
            result = session.execute(stmt)
            for row in result:
                if row.orbit_entity_id not in orbit_entity_id_ticker_map:
                    orbit_entity_id_ticker_map[row.orbit_entity_id] = []

                if row.ticker is not None:
                    orbit_entity_id_ticker_map[row.orbit_entity_id].append(row.ticker)
        for step_info, records in file_flow_info.items():
            for record in records:
                if 'extends' in record and record.get('extends') is not None:
                    tickers = set()
                    for i in record['extends']['perm_id_list']:
                        tickers.update(orbit_entity_id_ticker_map.get(i, []))
                    record['extends']['tickers'] = list(tickers)

                    record['extends']['report_type_id_list_str'] = [self.report_type_id_name_map.get(i) for i in record['extends']['report_type_id_list_str']]

        return file_flow_info

    def send_task(self, file_flow_info, tags, is_important, priority, spider_name_source_type):
        for step_str, records in file_flow_info.items():
            steps = step_str.split('@__@')
            start_stage = steps[0]
            target_stage = steps[1]
            x_spider_name = steps[2]

            if start_stage == 'success' or target_stage == 'success':
                self.all_stat_count['skip'] += len(records)
                logger.info(
                    f"{len(records)}--{start_stage}-{target_stage}-{x_spider_name} status: False, message: 'File has already completed the embedding stage.' ")
                continue

            if is_important:
                logger.info(f"is_important: {is_important} - {x_spider_name}")
                status, ids, message = self.file_handler.entry_point_urgent(records=records, start_stage=start_stage,
                                                                            target_stage=target_stage,
                                                                            tags=tags,
                                                                            tag=x_spider_name,
                                                                            priority=priority,
                                                                            source_type=spider_name_source_type[
                                                                                x_spider_name])
            else:
                status, ids, message = self.file_handler.entry_point(records=records, start_stage=start_stage,
                                                                     target_stage=target_stage, tags=tags,tag=x_spider_name,
                                                                     priority=priority,
                                                                     source_type=spider_name_source_type[x_spider_name])
            self.all_stat_count['file_flow'] += len(records)
            logger.info(f"{len(records)}--{start_stage}-{target_stage}-{x_spider_name} status: {status}, message: {message}")

    def op_meat_deduplicate_docs(self, docs, buffer_size=1000):
        buffer = []

        for doc in docs:
            buffer.append(doc)

            if len(buffer) >= buffer_size:
                doc_ids = [d['_id'] for d in buffer]
                with self.session_scope(use_session=self.Session2) as session:
                    existing_ids = session.query(self.op_meta.c.id).filter(self.op_meta.c.id.in_(doc_ids)).all()
                    existing_ids = {i[0] for i in existing_ids}
                for buffered_doc in buffer:
                    self.all_stat_count['all'] += 1
                    if buffered_doc['_id'] not in existing_ids:
                        yield buffered_doc

                buffer.clear()

        if buffer:
            doc_ids = [d['_id'] for d in buffer]
            with self.session_scope(use_session=self.Session2) as session:
                existing_ids = session.query(self.op_meta.c.id).filter(self.op_meta.c.id.in_(doc_ids)).all()
                existing_ids = {i[0] for i in existing_ids}
            for buffered_doc in buffer:
                self.all_stat_count['all'] += 1
                if buffered_doc['_id'] not in existing_ids:
                    yield buffered_doc

            buffer.clear()

    async def process_task_entry(self, source: str,
                           query: dict, tags: list[str], priority: str,
                           is_important: bool = False, custom_step: Optional[list[str]] = None, important_level = None, db_name: str = None):

        if not important_level or not isinstance(important_level, int):
            important_level = 0

        if important_level == 0:
            raise ValueError(f'important_level must be an integer (int) greater than 0. {important_level}')

        allowed_steps = {"convert", "extract", "embedding"}
        if custom_step is not None:
            if not isinstance(custom_step, list):
                raise ValueError("custom_step must be a list or None.")
            if len(custom_step) > 2:
                raise ValueError("custom_step can contain at most two elements.")
            for step in custom_step:
                if step not in allowed_steps:
                    raise ValueError(f"Invalid step '{step}'. Allowed steps are: {allowed_steps}")

        collection = self.mongo_client[db_name if db_name else "filing_reports"][source]
        spider_name_source_type = self.create_spider_name_source_type_map(collection, source)

        process_data = []
        perm_id_set = set()
        logger.info(f"load {source} data.")
        docs = collection.find(query).batch_size(1000)
        duplicate_docs = self.op_meat_deduplicate_docs(docs, buffer_size=self.max_batch_size) if not is_important else docs
        for doc in duplicate_docs:
            for orbit_entity_id in doc['x_orbit_data']['perm_id_list']:
                perm_id_set.add(orbit_entity_id)
            result_record = await self.data_processor.process(doc=doc, custom_process_step=custom_step, important_level=important_level)
            process_data.append(result_record)
            if len(process_data) >= self.max_batch_size:
                file_flow_info, xbrl_data, except_id_list, doc_error_list = self.data_processor.split_data_by_spider_name_and_step(
                    process_data)
                file_flow_info = self.update_extends_fields(list(perm_id_set), file_flow_info)
                self.all_stat_count['doc_error'] += len(doc_error_list)
                self.all_stat_count['step_error'] += len(except_id_list)
                self.all_stat_count['xbrl'] += len(xbrl_data)
                self.send_task(file_flow_info, tags, is_important, priority, spider_name_source_type)
                self.send_xbrl_data_to_mongo(xbrl_data)
                self.update_doc_status_to_convert(collection, doc_error_list)
                process_data.clear()
                perm_id_set.clear()

        if process_data:
            file_flow_info, xbrl_data, except_id_list, doc_error_list = self.data_processor.split_data_by_spider_name_and_step(
                process_data)
            file_flow_info = self.update_extends_fields(list(perm_id_set), file_flow_info)
            self.all_stat_count['doc_error'] += len(doc_error_list)
            self.all_stat_count['step_error'] += len(except_id_list)
            self.all_stat_count['xbrl'] += len(xbrl_data)
            self.send_task(file_flow_info, tags, is_important, priority, spider_name_source_type)
            self.send_xbrl_data_to_mongo(xbrl_data)
            self.update_doc_status_to_convert(collection, doc_error_list)
            process_data.clear()
            perm_id_set.clear()

        logger.info(f"finish processing {self.all_stat_count}. \n")
        self.all_stat_count = {'all': 0, 'skip': 0, 'doc_error': 0, 'step_error': 0, 'xbrl': 0, 'file_flow': 0}
