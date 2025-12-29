import requests

from requests import Request
import os, requests, json
import time
import traceback
from time import sleep
from lxml import etree
from typing import Literal


class ErpApi(object):
    URL = {
        "search_single_code": 'https://www.erp321.com/app/item/CombineSku/combinesku.aspx',
        "switch_ordinaryproinfo_enable": "https://api.erp321.com/erp/webapi/ItemApi/ItemSku/SetEnables",
        "switch_combproinfo_enable": "https://www.erp321.com/app/item/CombineSku/combinesku.aspx",
        "switch_ordinaryproinfo_stocksyn_enable": {
            "close": "https://api.erp321.com/erp/webapi/ItemApi/ItemSku/StockDisabledsV2",
            "open": "https://api.erp321.com/erp/webapi/ItemApi/ItemSku/StockEnablesV2"
        },
        "swich_combproinfo_stocksyn_enable": "https://www.erp321.com/app/item/CombineSku/combinesku.aspx",
        "search_stocksyn_log": "https://www.erp321.com/app/log/StockInventory.aspx",
        "batch_update_entity_code": "https://www.erp321.com/app/item/CombineSku/combinesku.aspx"
    }
    headers = {
        'post': {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.erp321.com',
            'referer': 'https://www.erp321.com/app/item/SkuStock/SycnInventory.aspx?_t=1688609930799&_h=550px&_float=true',
            'sec-ch-ua': '"Chromium";v="112", "Microsoft Edge";v="112", "Not:A-Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68',
            'x-requested-with': 'XMLHttpRequest',
        },
        'post1': {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.erp321.com',
            'referer': 'https://www.erp321.com/app/item/CombineSku/combinesku.aspx?owner_co_id=10174711&authorize_co_id=10174711',
            'sec-ch-ua': '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
            'x-requested-with': 'XMLHttpRequest',
        },
        'pt_post': {
            'accept': 'application/json',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'content-type': 'application/json; charset=utf-8',
            'origin': 'https://src.erp321.com',
            'sec-ch-ua': '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'u_sso_token': '',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0',
            'webbox-route-path': '/erp-web-group/erp-scm-goods/',
        }
    }

    enabled_1 = {
        "启用": 1,
        "备用": 0,
        "禁用": -1
    }

    def __init__(self, u, p):
        self.session = requests.Session()
        self.uid = None
        self.coid = None
        self.coname = None
        self.uname = None
        self.phone = None
        self.login_info = self.login(u, p)
        self.shops = self.get_ShopId()
        self.init_VIEWSTATE()

    def ERP_Request(self, request):
        resp = None
        for i in range(3):
            try:
                resp = self.session.send(self.session.prepare_request(request))
                break
            except Exception as e:
                if i == 2:
                    print(e)
                    # traceback.print_exc()
                    raise ValueError(request.url + ":接口地址调用异常")
        return resp

    def init_VIEWSTATE(self):
        self.search_single_code_v1, self.search_single_code_v2, self.search_single_code_v3 = self.get_viewstate(
            self.URL['search_single_code'])
        self.switch_combproinfo_enable_v1, self.switch_combproinfo_enable_v2, self.switch_combproinfo_enable_v3 = self.get_viewstate(
            self.URL['switch_combproinfo_enable'])
        self.swich_combproinfo_stocksyn_enable_v1, self.swich_combproinfo_stocksyn_enable_v2, self.swich_combproinfo_stocksyn_enable_v3 = self.get_viewstate(
            self.URL['swich_combproinfo_stocksyn_enable'])
        self.search_stocksyn_log_v1, self.search_stocksyn_log_v2, self.search_stocksyn_log_v3 = self.get_viewstate(
            self.URL['search_stocksyn_log'])
        self.batch_update_entity_code_v1, self.batch_update_entity_code_v2, self.batch_update_entity_code_v3 = self.get_viewstate(
            self.URL['batch_update_entity_code'])

    def get_now_ts___(self):
        return int(time.time() * 1000)

    def login(self, uname, upwd):
        res = self.ERP_Request(Request(
            'post',
            'https://api.erp321.com/erp/webapi/UserApi/WebLogin/Passport',
            json={"data": {"account": uname, "password": upwd,
                           "j_d_3": "TAUYIQUBK73IYCNAN3GIALFKJ22SCTTQW7FVGOSMUOKECJOUO45YRGGGRR44W4IGP4MZPCIEBUQELQXC53HBO2NOPM",
                           "v_d_144": "1678719265075_19e997685c9b10b0a21d7a42af3120d5",
                           "isApp": False}, "ipAddress": ""},
            headers={
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/json',
                'jst-appkey': 'web_login',
                'jst-pv': '1.0.0',
                'jst-screen': '1440;2560',
                'jst-sdkv': '1.0.0',
                'jst-static': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
                'origin': 'https://www.erp321.com',
                'referer': 'https://www.erp321.com/',
                'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
            }
        )).json()
        if res['code'] != 0:
            raise ValueError('ERP登录失败:' + str(res))
        self.uid = str(res['cookie']['u_id'])
        self.coid = str(res['cookie']['u_co_id'])
        self.uname = str(requests.utils.unquote(res['cookie']['u_name']))
        self.coname = str(requests.utils.unquote(res['cookie']['u_co_name']))
        self.phone = str(res['cookie']['u_lid'])
        print('登录成功!', f'公司id：{self.coid}'
              , f"手机号码：{self.phone}",
              f'用户id：{self.uid}',
              f"公司名称：{self.coname}",
              f'用户：{self.uname}')
        return '\n'.join(['登录成功!', f'公司id：{self.coid}', f"手机号码：{self.phone}", f'用户id：{self.uid}',
                          f"公司名称：{self.coname}",
                          f'用户：{self.uname}'])

    def get_viewstate(self, url):  # 获取__VIEWSTATE和__VIEWSTATEGENERATOR
        # 获取__VIEWSTATE和__VIEWSTATEGENERATOR
        res = self.ERP_Request(Request('GET', url, headers={}))
        etree_xpath = etree.HTML(res.text)
        __VIEWSTATE = etree_xpath.xpath("//*[@id='__VIEWSTATE']/@value")[0]
        __VIEWSTATEGENERATOR = etree_xpath.xpath("//*[@id='__VIEWSTATEGENERATOR']/@value")[0]
        __EVENTVALIDATION = etree_xpath.xpath("//*[@id='__EVENTVALIDATION']/@value")[0] if len(
            etree_xpath.xpath("//*[@id='__EVENTVALIDATION']/@value")) > 0 else None
        return __VIEWSTATE, __VIEWSTATEGENERATOR, __EVENTVALIDATION

    def get_ShopId(self):
        '''
        :param shopName: 店铺名
        :return shopName=str 返回店铺id shopName=list 返回 对应字典
        '''
        url = f"https://api.erp321.com/erp/webapi/ShopApi/ShopPage/GetShopList"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'access-control-allow-origin': '*',
            'content-type': 'application/json; charset=UTF-8',
            'origin': 'https://src.erp321.com',
            'referer': 'https://src.erp321.com/',
            'sec-ch-ua': '"Not_A Brand";v="99", "Microsoft Edge";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.78',
        }
        cjson = {"ip": "", "coid": self.coid, "uid": self.uid, "data": {"groupId": "", "shopName": ""},
                 "page": {"currentPage": 1, "pageSize": 200}}
        r = self.ERP_Request(Request('POST', url=url, headers=headers, json=cjson))
        if isinstance(r, str):
            r = json.loads(r.text)
        else:
            r = r.json()
        if r['code'] != 0: raise ValueError(f"ERP查询店铺ID出错 {r}")
        r_dct = {i['shopName']: i['shopId'] for i in r['data']}
        return r_dct

    def submit_img_erp(self, path):
        '''上传图片导普通商品资料图库'''
        uid = self.uid
        headers = {
            "post": {
                'Accept': 'application/json',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Content-Type': 'application/json; charset=utf-8',
                'Gwfp': 'c5f15e0836debe29da46d05a4d62e3dc',
                'Origin': 'https://src.erp321.com',
                'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Microsoft Edge";v="110"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.46',
                'X-Requested-With': 'XMLHttpRequest',
            },
            "post1": {
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Connection': 'keep-alive',
                'Host': 'jst-erp-public.oss-cn-hangzhou.aliyuncs.com',
                'Origin': 'https://src.erp321.com',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183',
                'sec-ch-ua': '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"'
            }
        }
        # 第一段
        a_url = f'https://api.erp321.com/erp/webapi/ItemApi/CompanyInfo/GetOssSignature?owner_co_id={self.coid}&authorize_co_id={self.coid}'
        a_ijson = {"ip": "", "uid": uid, "coid": self.coid}
        a_r = self.ERP_Request(Request('post', a_url, json=a_ijson, headers=headers['post']))
        if a_r.json()['code'] != 0:
            raise ValueError(a_r.status_code, '图片提交第一段请求失败!', a_r.text)
        # 第二段
        b_url = 'https://jst-erp-public.oss-cn-hangzhou.aliyuncs.com/'
        key = a_r.json()['data']['dir'] + str(int(round(time.time() * 1000))) + '.png'
        data = {
            'key': key,
            'OSSAccessKeyId': a_r.json()['data']['accessId'],
            'policy': a_r.json()['data']['policy'],
            'Signature': a_r.json()['data']['signature']
        }
        b_r = requests.post(b_url, data=data, files={'file': open(path, 'rb')}, headers=headers['post1'])
        if b_r.status_code != 204:
            raise ValueError(b_r.status_code, '图片提交第二段请求失败!', b_r.text)
        result = "https://images-erp.sursung.com/" + key
        print(path, '上传成功:', result)
        return result

    def search_takepartcomb_code(self, data: list, enable: list, search_type: Literal['单件', '多件']) -> list:
        '''
        通过参与组合编码搜索
        :param data: 白坯+烫画
        :param enable: ["启用","禁用","备用"]
        :return: 单件编码
        '''
        addstr = "-CP" if search_type == "单件" else ""
        page = 1
        result = []
        while True:
            print('通过参与组合编码搜索', '第', page, '页')
            current_enable = ','.join([str(self.enabled_1[x]) for x in enable])
            params = {
                'owner_co_id': self.coid,
                'authorize_co_id': self.coid,
                'ts___': self.get_now_ts___,
                'am___': 'LoadDataToJSON',
            }
            data = {
                '__VIEWSTATE': self.search_single_code_v1,
                '__VIEWSTATEGENERATOR': self.search_single_code_v2,
                'owner_co_id': self.coid,
                'authorize_co_id': self.coid,
                'sku_id': '',
                'i_id': '',
                'name': '',
                'enty_sku_id': '',
                'short_name': '',
                'properties_value': '',
                'brand': '',
                'labels_search': '',
                'labels_exclude_search': '',
                'sku_code': '',
                'src_sku_id': ','.join(data),
                'cost_price_type': '1',
                'cost_price': [
                    '',
                    '',
                ],
                'vc_name': '',
                'enabled': '',
                'enabled_name': '',
                'is_tm_direct': '',
                'wmsCoId': '',
                'stock_disabled': '',
                'item_auto': '',
                'remark': '',
                '$AppendSearch_Input_41620': '',
                '$AppendSearch_Input_41621': '',
                '$AppendSearch_Input_823': '',
                '$AppendSearch_Input_824': '',
                '_jt_page_count_enabled': '',
                '_jt_page_size': '500',
                '_jt_page_action': '2',
                '_cbb_brand': '',
                '_cbb_vc_name': '',
                '_cbb_enabled_name': '',
                '__CALLBACKID': 'JTable1',
                '__CALLBACKPARAM': json.dumps(
                    {"Method": "LoadDataToJSON", "Args": [str(page), json.dumps(
                        [{"k": "src_sku_id", "v": ','.join(data), "c": "like"},
                         {"k": "enabled", "v": current_enable, "c": "@="},
                         {"k": "cost_price_type", "v": "1", "c": "="}]), "{}"]}
                ),
                '__EVENTVALIDATION': self.search_single_code_v3,
            }
            resp = self.ERP_Request(Request(method='POST',
                                            url=self.URL['search_single_code'],
                                            headers=self.headers['post1'],
                                            params=params,
                                            data=data))
            resp_json = json.loads(resp.text[2:])
            datas = json.loads(resp_json['ReturnValue'])['datas']
            if datas == []: break
            result += [str(x['sku_id']) + addstr for x in datas if x['sku_id']]
            page += 1
        return result

    def switch_ordinaryproinfo_status_enable(self, data: list, enable: Literal['启用', '禁用', '备用']) -> None:
        '''开关普通商品资料 状态'''
        enableType = self.enabled_1[enable]
        params = {
            'owner_co_id': self.coid,
            'authorize_co_id': self.coid,
        }
        json_data = {
            'ip': '',
            'uid': self.uid,
            'coid': self.coid,
            'data': {
                'enableType': enableType,
                'ids': [{'sku_id': x} for x in data],
                'filterType': 1,
                'isIgnoreCheckItemSkuSyncStockSetting': True,
            },
        }
        resp = self.ERP_Request(Request(method='POST',
                                        url=self.URL['switch_ordinaryproinfo_enable'],
                                        headers=self.headers['pt_post'],
                                        params=params,
                                        json=json_data))
        print(resp.json())

    def switch_combproinfo_status_enable(self, data: list, enable: Literal['启用', '禁用', '备用']) -> None:
        '''开关组合商品资料 状态'''
        enableType = self.enabled_1[enable]
        params = {
            'owner_co_id': self.coid,
            'authorize_co_id': self.coid,
            'ts___': self.get_now_ts___,
            'am___': 'SetEnables',
        }
        data = {
            '__VIEWSTATE': self.switch_combproinfo_enable_v1,
            '__VIEWSTATEGENERATOR': self.switch_combproinfo_enable_v2,
            'owner_co_id': self.coid,
            'authorize_co_id': self.coid,
            'sku_id': ','.join(data),
            'i_id': '',
            'name': '',
            'enty_sku_id': '',
            'short_name': '',
            'properties_value': '',
            'brand': '',
            'labels_search': '',
            'labels_exclude_search': '',
            'sku_code': '',
            'src_sku_id': '',
            'cost_price_type': '1',
            'cost_price': [
                '',
                '',
            ],
            'vc_name': '',
            'enabled': '-1',
            'enabled_name': '启用,备用,禁用',
            'is_tm_direct': '',
            'wmsCoId': '',
            'stock_disabled': '',
            'item_auto': '',
            'remark': '',
            '$AppendSearch_Input_41620': '',
            '$AppendSearch_Input_41621': '',
            '$AppendSearch_Input_823': '',
            '$AppendSearch_Input_824': '',
            '_jt_page_count_enabled': '',
            '_jt_page_increament_enabled': 'true',
            '_jt_page_increament_page_mode': '',
            '_jt_page_increament_key_value': '',
            '_jt_page_increament_business_values': '',
            '_jt_page_increament_key_name': 'sku_id',
            '_jt_page_size': '500',
            '_cbb_brand': '',
            '_cbb_vc_name': '',
            '__CALLBACKID': 'JTable1',
            '__CALLBACKPARAM': json.dumps(
                {"Method": "SetEnables", "Args": [','.join(data), str(enableType)], "CallControl": "{page}"}),
            '__EVENTVALIDATION': self.switch_combproinfo_enable_v3
        }
        resp = self.ERP_Request(Request(method='POST',
                                        url=self.URL['switch_combproinfo_enable'],
                                        headers=self.headers['post1'],
                                        params=params,
                                        data=data))
        print(resp.text[2:])

    def switch_ordinaryproinfo_stocksyn_enable(self, data: list, enable: Literal['启用', '禁用']) -> None:
        '''开关普通商品资料 库存同步'''
        if enable == '启用':
            url = self.URL['switch_ordinaryproinfo_stocksyn_enable']['open']
        elif enable == '禁用':
            url = self.URL['switch_ordinaryproinfo_stocksyn_enable']['close']
        params = {
            'owner_co_id': self.coid,
            'authorize_co_id': self.coid
        }
        json_data = {
            'ip': '',
            'uid': self.uid,
            'coid': self.coid,
            'data': {
                'ids': [{'sku_id': x} for x in data],
                'filterType': 1,
                'isIgnoreCheckItemSkuSyncStockSetting': True,
            },
        }
        resp = self.ERP_Request(Request(method='POST',
                                        url=url,
                                        headers=self.headers['pt_post'],
                                        params=params,
                                        json=json_data))
        print(resp.json())

    def swich_combproinfo_stocksyn_enable(self, data: list, enable: Literal['启用', '禁用']) -> None:
        '''开关组合商品资料 库存同步'''
        if enable == '启用':
            am___ = 'StockEnables'
        elif enable == '禁用':
            am___ = 'StockDisableds'
        params = {
            'owner_co_id': self.coid,
            'authorize_co_id': self.coid,
            'ts___': self.get_now_ts___,
            'am___': am___
        }
        data = {
            '__VIEWSTATE': self.swich_combproinfo_stocksyn_enable_v1,
            '__VIEWSTATEGENERATOR': self.swich_combproinfo_stocksyn_enable_v2,
            'owner_co_id': self.coid,
            'authorize_co_id': self.coid,
            'sku_id': ','.join(data),
            'i_id': '',
            'name': '',
            'enty_sku_id': '',
            'short_name': '',
            'properties_value': '',
            'brand': '',
            'labels_search': '',
            'labels_exclude_search': '',
            'sku_code': '',
            'src_sku_id': '',
            'cost_price_type': '1',
            'cost_price': [
                '',
                '',
            ],
            'vc_name': '',
            'enabled': '1,0,-1',
            'enabled_name': '启用,备用,禁用',
            'is_tm_direct': '',
            'wmsCoId': '',
            'stock_disabled': '',
            'item_auto': '',
            'remark': '',
            '$AppendSearch_Input_41620': '',
            '$AppendSearch_Input_41621': '',
            '$AppendSearch_Input_823': '',
            '$AppendSearch_Input_824': '',
            '_jt_page_count_enabled': '',
            '_jt_page_increament_enabled': 'true',
            '_jt_page_increament_page_mode': '',
            '_jt_page_increament_key_value': '',
            '_jt_page_increament_business_values': '',
            '_jt_page_increament_key_name': 'sku_id',
            '_jt_page_size': '500',
            '_cbb_brand': '',
            '_cbb_vc_name': '',
            '__CALLBACKID': 'JTable1',
            '__CALLBACKPARAM': json.dumps({"Method": am___, "Args": [','.join(data)], "CallControl": "{page}"}),
            '__EVENTVALIDATION': self.swich_combproinfo_stocksyn_enable_v3
        }
        resp = self.ERP_Request(Request(method='POST',
                                        url=self.URL['swich_combproinfo_stocksyn_enable'],
                                        headers=self.headers['post1'],
                                        params=params,
                                        data=data))
        print(resp.text[2:])

    def search_stocksyn_log(self, i_ids: list = None, sku_ids: list = None, syn_st: str = None, syn_et: str = None,
                            qty_s: int = None, qty_e: int = None, shopnames: list = None, shop_sku_id: str = None,
                            syn_status: str = None) -> list:
        '''
        搜索库存同步日志
        :param i_ids: 款式编码
        :param sku_ids: 商品编码
        :param syn_st: 同步开始日期
        :param syn_et: 同步结束日期
        :param qty_s: 库存数量Min
        :param qty_e: 库存数量Max
        :param shopnames: 店铺名称
        :param shop_sku_id: 店铺商品编码
        :param syn_status: 同步状态
        :return: list
        '''
        params = {
            'ts___': self.get_now_ts___,
            'am___': 'LoadDataToJSON',
        }
        status = {'等待同步': 'WAITING', '已同步': 'SUCCESS',
                  '异常': 'FAILED', '禁止同步': 'DISABLED',
                  '取消同步': 'WEB_CANCEL', '库存变化小，不同步': 'CANCEL',
                  '冻结同步': 'FROZEN', '异常（预处理）': 'FAILED_PROCESS'}
        args_params = []
        if i_ids:
            args_params.append({"k": "i_id", "v": ','.join(i_ids), "c": "like"})
        if syn_status:
            args_params.append({"k": "status", "v": status[syn_status], "c": "="})
        if sku_ids:
            args_params.append({"k": "sku_id", "v": ','.join(sku_ids), "c": "like"})
        if shopnames:
            args_params.append({"k": "shop_id", "v": ','.join([str(self.shops[x]) for x in shopnames]), "c": "@="})
        if syn_st:
            args_params.append({"k": "modified", "v": syn_st, "c": ">=", "t": "date"})
        if syn_et:
            args_params.append({"k": "modified", "v": f"{syn_et} 23:59:59.998", "c": "<=", "t": "date"})
        if qty_s:
            args_params.append({"k": "qty", "v": str(qty_s), "c": ">="})
        if qty_e:
            args_params.append({"k": "qty", "v": str(qty_e), "c": "<="})
        if shop_sku_id:
            args_params.append({"k": "shop_sku_id", "v": shop_sku_id, "c": "="})
        data = {
            '__VIEWSTATE': self.search_stocksyn_log_v1,
            '__VIEWSTATEGENERATOR': self.search_stocksyn_log_v2,
            'i_id': ','.join(i_ids) if i_ids else '',
            'sku_id': ','.join(sku_ids) if sku_ids else '',
            'created': '',
            'status': status[syn_status] if syn_status else '',
            'remark': '',
            'result': '',
            'modified': [syn_st if syn_st else '', syn_et if syn_et else ''],
            'qty': [str(qty_s) if qty_s else '', str(qty_e) if qty_e else ''],
            'shop_id': ','.join([str(self.shops[x]) for x in shopnames]) if shopnames else '',
            'shop_name': ",".join(shopnames) if shopnames else '',
            'shop_sku_id': shop_sku_id if shop_sku_id else '',
            'shop_i_id': '',
            'others': '',
            '_jt_page_count_enabled': '',
            '_jt_page_size': '100',
            '__CALLBACKID': 'JTable1',
            '__CALLBACKPARAM': json.dumps({"Method": "LoadDataToJSON", "Args": ["1", json.dumps(args_params), "{}"]})
        }
        resp = self.ERP_Request(Request(
            method='POST',
            url=self.URL['search_stocksyn_log'],
            headers=self.headers['post1'],
            params=params,
            data=data))
        print(resp.text[2:])

    def batch_update_entity_code(self, sku_list: list):
        '''批量更新实体编码'''
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://dopre.jushuitan.com',
            'priority': 'u=1, i',
            'referer': 'https://dopre.jushuitan.com/app/item/CombineSku/combinesku.aspx?owner_co_id=10174711&authorize_co_id=10174711',
            'sec-ch-ua': '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
            'x-requested-with': 'XMLHttpRequest',
        }
        params = {
            'owner_co_id': self.coid,
            'authorize_co_id': self.coid,
            'ts___': self.get_now_ts___(),
            'am___': 'UpdateEnty',
        }
        data = {
            '__VIEWSTATE': self.batch_update_entity_code_v1,
            '__VIEWSTATEGENERATOR': self.batch_update_entity_code_v2,
            'owner_co_id': self.coid,
            'authorize_co_id': self.coid,
            'sku_id': ','.join([x.strip() for x in sku_list]),
            'i_id': '',
            'name': '',
            'enty_sku_id': '',
            'short_name': '',
            'properties_value': '',
            'brand': '',
            'labels_search': '',
            'labels_exclude_search': '',
            'sku_code': '',
            'src_sku_id': '',
            'cost_price_type': '1',
            'cost_price': [
                '',
                '',
            ],
            'vc_name': '',
            'enabled': '1',
            'enabled_name': '启用',
            'is_tm_direct': '',
            'wmsCoId': '',
            'stock_disabled': '',
            'item_auto': '',
            'remark': '',
            '$AppendSearch_Input_41620': '',
            '$AppendSearch_Input_41621': '',
            '$AppendSearch_Input_823': '',
            '$AppendSearch_Input_824': '',
            '_jt_page_count_enabled': '',
            '_jt_page_increament_enabled': 'true',
            '_jt_page_increament_page_mode': '',
            '_jt_page_increament_key_value': '',
            '_jt_page_increament_business_values': '',
            '_jt_page_increament_key_name': 'sku_id',
            '_jt_page_size': '50',
            '_cbb_brand': '',
            '_cbb_vc_name': '',
            '_cbb_enabled_name': '',
            '__CALLBACKID': 'JTable1',
            '__CALLBACKPARAM': json.dumps(
                {"Method": "UpdateEnty", "Args": ["weight,cost_price", ','.join([x.strip() for x in sku_list]), "true"],
                 "CallControl": "{page}"}),
            '__EVENTVALIDATION': self.batch_update_entity_code_v3
        }
        resp = self.ERP_Request(Request(
            method='POST',
            url=self.URL['batch_update_entity_code'],
            headers=headers,
            params=params,
            data=data
        ))
        resp_json = json.loads(resp.text[2:])
        print(resp_json)


if __name__ == "__main__":
    ef = ErpApi(u="", p="")
    # 0.批量更新实体编码
    import pandas as pd
    df=pd.read_excel(r"/Users/hwj/Desktop/缺成本价的--商品资料_20240428203443_40034778_1.xlsx").to_dict(orient='records')
    data = [x['商品编码'].strip().replace("-CP","") for x in df]
    from lbw_math import subset
    for x in subset(data, 5000):
        ef.batch_update_entity_code(x)
        time.sleep(30)

    # 1.通过白坯+烫画 搜索 单件编码
    # single_data=ef.search_takepartcomb_code(['中国醒狮'], ['启用', '禁用', '备用'],search_type="单件")
    # print(single_data,'\n')

    # 2.通过单件编码 搜索多件编码
    # muitple_data = ef.search_takepartcomb_code(single_data, ['启用', '禁用', '备用'], search_type="多件")
    # print(muitple_data,'\n')

    # 3.普通（开启，关闭）库存同步
    # ef.switch_ordinaryproinfo_stocksyn_enable(data=['S-男合体T-白色-BANG-CP', 'S-男合体T-黑色-BANG-CP'], enable='禁用')

    # 4.组合（开启，关闭）库存同步
    # ef.swich_combproinfo_stocksyn_enable(data=['S-男合体T-白色-BANG', 'S-男合体T-黑色-BANG'], enable='启用')

    # 5.搜索店铺商品资料

    # 6.库存同步

    # 7.搜索库存同步日志
    # ef.search_stocksyn_log()

    # 8.普通商品资料 （启用，关闭）
    # ef.switch_ordinaryproinfo_status_enable(data=['S-男合体T-白色-BANG-CP', 'S-男合体T-黑色-BANG-CP'], enable='启用')

    # 9.组合商品资料 （启用，关闭）
    # ef.switch_combproinfo_status_enable(data=['S-男合体T-白色-BANG', 'S-男合体T-黑色-BANG'], enable='启用')

    # 10.导入虚拟库存
