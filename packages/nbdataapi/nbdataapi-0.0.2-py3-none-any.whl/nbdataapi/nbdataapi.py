import requests
import json
import time


class FeishuWorksheet:
    '''飞书工作表类 提供关于在线表格的操作'''

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.headers = {"Content-Type": "application/json"}

    def make_tenant_access_token(self):
        '''获取飞书租户访问令牌'''
        token_url = r"https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }
        response = requests.post(token_url, headers=self.headers, json=data)
        return response.json()["tenant_access_token"]
    
    def worksheet_message(self, Spreadsheet: str, sheetid: str):
        '''获取工作表信息\n
        参数：\n
        Spreadsheet: 表格token\n
        sheetid: 工作表id\n
        
        返回：\n
        row_count: 工作表的行数\n
        column_count: 工作表的列数
        '''
        #  【1】获取访问令牌
        access_token = self.make_tenant_access_token()

        #  【2】设置主要参数
        access_token = access_token  
        spreadsheetToken = Spreadsheet  # 表格token
        self.headers["Authorization"] = f"Bearer {access_token}"

        # 【3】设置请求参数
        params = {
            "spreadsheetToken": spreadsheetToken,
            "sheet_id": sheetid,
        }

        # API URL
        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheetToken}/sheets/{sheetid}"
        res = requests.get(url, headers=self.headers, params=params)

        del self.headers["Authorization"]
        
        if res.status_code == 200:
            return res.json()["data"]["sheet"]["grid_properties"]
        else:
            print("获取飞书在线表格信息失败")
            return res.json()
    
    def find_data(self, Spreadsheet: str, sheetid: str, ranges: str, findstr: str):
        '''实现在表格指定区域查找文本所在的位置\n
        参数：\n
        Spreadsheet: 表格token\n
        sheetid: 工作表id\n
        ranges: 读取范围,例如：'A1:D10'\n
        findstr: 查找的文本
        '''
        #  【1】获取访问令牌
        access_token = self.make_tenant_access_token()

        #  【2】设置主要参数
        access_token = access_token  
        spreadsheetToken = Spreadsheet  # 表格token
        ranges = f"{sheetid}!{ranges}" # 读取范围
        self.headers["Authorization"] = f"Bearer {access_token}"

        # 【3】设置请求参数
        data = {
            "spreadsheetToken": spreadsheetToken,
            "find_condition": {
                "range": ranges,
                "match_case": True,
                "match_entire_cell": False,
                "search_by_regex": False,
                "include_formulas": False
                },
            "find": findstr
        }

        # API URL
        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheetToken}/sheets/{sheetid}/find"
        res = requests.post(url, headers=self.headers, json=data)

        del self.headers["Authorization"]

        if res.status_code == 200:
            return res.json()['data']['find_result']['matched_cells']
        else:
            print("飞书在线表格中查找文本失败")
            return res.json()

    def get_data(self, Spreadsheet: str, sheetid: str, ranges: str):
        '''获取飞书在线表格数据\n
        参数：\n
        Spreadsheet: 表格token\n
        sheetid: 工作表id\n
        ranges: 读取范围
        '''
        #  【1】获取访问令牌
        access_token = self.make_tenant_access_token()

        #  【2】设置主要参数
        access_token = access_token  
        spreadsheetToken = Spreadsheet  # 表格token
        ranges = f"{sheetid}!{ranges}" # 读取范围
        self.headers["Authorization"] = f"Bearer {access_token}"

        # 【3】设置请求参数
        params = {
            "spreadsheetToken": spreadsheetToken,
            "ranges": ranges
        }

        # API URL
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheetToken}/values_batch_get"
        res = requests.get(url, headers=self.headers, params=params)

        # print(res.json())

        del self.headers["Authorization"]

        if res.status_code == 200:
            return res.json()['data']['valueRanges'][0]['values']
        else:
            print("获取飞书在线表格数据失败")
            return res.json()

    def write_data(self, Spreadsheet: str, sheetid: str, ranges: str, data: list):
        '''写入数据到飞书在线表格\n
        参数：\n
        Spreadsheet: 表格token\n
        sheetid: 工作表id\n
        ranges: 读取范围
        '''
        #  【1】获取访问令牌
        access_token = self.make_tenant_access_token()

        #  【2】设置主要参数
        access_token = access_token  
        spreadsheetToken = Spreadsheet  # 表格token
        ranges = f"{sheetid}!{ranges}" # 读取范围
        self.headers["Authorization"] = f"Bearer {access_token}"

        # 【3】设置请求参数
        params = {
            "spreadsheetToken": spreadsheetToken,
             "valueRange": {
                "range": ranges,
                "values": data
             }
        }

        # API URL
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheetToken}/values"
        res = requests.put(url, headers=self.headers, json=params)

        del self.headers["Authorization"]

        res.json()

        if res.status_code == 200:
            return res.json()
        else:
            print("写入飞书在线表格数据失败")
            return res.json()

    