# -*- coding:utf-8 -*-
# ProjectName：huojiweiguoba
# FileName：feishu_sdk.py
# Time：2025/5/5 上午10:51
# Author：侯文杰
# IDE：PyCharm
import os
from pathlib import Path

import requests
from requests_toolbelt import MultipartEncoder
from huojiweiguoba.decorator import retry


class FeiShuOpenApi:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.ask = requests.sessions.Session()
        self.authorization = ""
        self.headers = {"Content-Type": "application/json; charset=utf-8"}
        self.auth()

    def _verify_response(self, resp: dict, title: str):
        if resp["code"] != 0:
            raise ValueError(f"[飞书API] {title}:{resp}")

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def auth(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        json_data = {"app_id": self.app_id, "app_secret": self.app_secret}
        resp = self.ask.post(url=url, json=json_data, headers=self.headers)
        resp_json = resp.json()
        if resp_json["code"] != 0:
            raise ValueError(resp_json["msg"])
        self.authorization = "Bearer " + resp_json["tenant_access_token"]
        self.headers["Authorization"] = "Bearer " + resp_json["tenant_access_token"]
        print(f"[飞书API] 授权成功！{resp_json}")

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def _append_multi_table_datas(self, multi_id: str, table_id: str, fields_data: list):
        '''新增多维表格数据'''
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{multi_id}/tables/{table_id}/records/batch_create"
        resp = self.ask.post(url=url, headers=self.headers, json={"records": fields_data}).json()
        self._verify_response(resp, "添加多维表格数据")
        return resp["data"]

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def _query_tables_datas(self, multi_id: str, table_id: str, view_id: str, filter_data: dict = None,
                            page_size: int = 500, page_token: str = None):
        '''查询多维表格'''
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{multi_id}/tables/{table_id}/records/search"
        json_params = {"view_id": view_id, }
        if filter_data:
            json_params["filter"] = filter_data
        params = {
            "page_size": page_size
        }
        if page_token:
            params["page_token"] = page_token
        resp = self.ask.post(url=url, headers=self.headers, json=json_params, params=params).json()
        self._verify_response(resp, "查询多维表格")
        return resp['data']

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def _update_multi_dimension_table_single_data(self, multi_id: str, table_id: str, record_id: str,
                                                  fields_data: dict):
        '''更新多维表格单条数据'''
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{multi_id}/tables/{table_id}/records/{record_id}"
        resp = self.ask.put(url=url, headers=self.headers, json={"fields": fields_data}).json()
        self._verify_response(resp, "更新多维表格单条数据")
        # {'code': 0, 'data': {'record': {'fields': {'状态': '错误'}, 'id': 'recuFWBX2rFDdT', 'record_id': 'recuFWBX2rFDdT'}}, 'msg': 'success'}
        return resp['data']

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def _update_multi_dimension_table_many_data(self, multi_id: str, table_id: str, fields_data: list):
        '''更新多维表格多条数据'''
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{multi_id}/tables/{table_id}/records/batch_update"
        resp = self.ask.post(url=url, headers=self.headers, json={"records": fields_data}).json()
        self._verify_response(resp, "更新多维表格多条数据")
        return resp['data']

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def _query_multi_tables(self, multi_id: str):
        '''列出-多维表格-数据表'''
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{multi_id}/tables"
        params = {"page_size": 100}
        resp = self.ask.get(url=url, headers=self.headers, params=params).json()
        self._verify_response(resp, "列出-多维表格-数据表")
        return resp['data']

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def _query_multi_tables_views(self, multi_id: str, table_id: str):
        '''列出-多维表格-数据表-视图'''
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{multi_id}/tables/{table_id}/views"
        params = {"page_size": 100}
        resp = self.ask.get(url=url, headers=self.headers, params=params).json()
        self._verify_response(resp, "列出-多维表格-数据表-视图")
        return resp['data']

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def _query_root_folder(self):
        '''获取我的空间（root folder）元数据'''
        url = f"https://open.feishu.cn/open-apis/drive/explorer/v2/root_folder/meta"
        resp = self.ask.get(url=url, headers=self.headers).json()
        self._verify_response(resp, "获取我的空间（root folder）元数据")
        return resp['data']

    @retry(max_retries=5, wait_time=2, exception_items=[
        {"error_type": requests.exceptions.ConnectionError},
        {"error_type": requests.exceptions.ReadTimeout},
        {"error_type": requests.exceptions.JSONDecodeError},
        {"error_msg": "request trigger frequency limit"}
    ])
    def _upload_cloud_document(self, file_path: str, parent_node: str, parent_type: str = 'bitable_image'):
        '''上传文件到云文档（多维表格）'''
        url = f"https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
        file_size = os.path.getsize(file_path)
        form = {
            'file_name': Path(file_path).name,
            'parent_type': parent_type,
            'parent_node': parent_node,
            'size': str(file_size),
            'file': (open(file_path, 'rb'))
        }
        multi_form = MultipartEncoder(form)
        headers = self.headers.copy()
        headers['Content-Type'] = multi_form.content_type
        resp = self.ask.post(url, headers=headers, data=multi_form).json()
        self._verify_response(resp, "上传文件到云文档")
        return resp['data']


class FeiShuConnector(FeiShuOpenApi):
    '''连接器'''

    def __init__(self, app_id: str, app_secret: str, multi_id: str):
        super().__init__(app_id, app_secret)
        self.multi_id = multi_id
        self.table_tree = None  # 表格树

        # loading
        self.tree()

    def tree(self):
        '''获取表格-数据表结构'''
        # 1.数据表
        tables_resp = self._query_multi_tables(self.multi_id)
        tables_items = {x['name']: x for x in tables_resp['items']}
        # 2.所有数据表-所有视图
        for k, v in tables_items.items():
            views_resp = self._query_multi_tables_views(self.multi_id, v['table_id'])
            views_items = {x['view_name']: x for x in views_resp['items']}
            tables_items[k]['views'] = views_items
        self.table_tree = tables_items

    def query(self, table_name: str, view_name: str, filter_data: dict = None):
        '''查询表格-视图数据'''
        assert table_name in self.table_tree, f"[飞书API] 表格不存在：{table_name}"
        assert view_name in self.table_tree[table_name]['views'], f"[飞书API] [{table_name}]视图不存在：{view_name}"
        table_id = self.table_tree[table_name]['table_id']
        view_id = self.table_tree[table_name]['views'][view_name]['view_id']

        result_datas = {"items": []}

        page_token = None
        while True:
            resp = self._query_tables_datas(self.multi_id, table_id, view_id, filter_data, page_token=page_token)
            result_datas['items'].extend(resp['items'])
            if "page_token" in resp:
                page_token = resp["page_token"]
            else:
                break
        return result_datas

    def update_single(self, table_name: str, record_id: str, fields_data: dict):
        assert table_name in self.table_tree, f"[飞书API] 表格不存在：{table_name}"
        table_id = self.table_tree[table_name]['table_id']
        resp = self._update_multi_dimension_table_single_data(self.multi_id, table_id, record_id, fields_data)
        return resp

    def append_many(self, table_name: str, fields_data: list):
        assert table_name in self.table_tree, f"[飞书API] 表格不存在：{table_name}"
        table_id = self.table_tree[table_name]['table_id']
        resp = self._append_multi_table_datas(self.multi_id, table_id, fields_data)
        return resp

    def update_many(self, table_name: str, fields_data: list):
        assert table_name in self.table_tree, f"[飞书API] 表格不存在：{table_name}"
        table_id = self.table_tree[table_name]['table_id']
        resp = self._update_multi_dimension_table_many_data(self.multi_id, table_id, fields_data)
        return resp


if __name__ == "__main__":
    app_id, app_secret, multi_id = None, None, None
    yfs = FeiShuConnector(app_id, app_secret, multi_id)
    yfs.auth()

    filter_data = {
        "conjunction": "and",
        "conditions": []
    }
    result = yfs.query("订单记录", "表格", filter_data)
    print(len(result['items']))