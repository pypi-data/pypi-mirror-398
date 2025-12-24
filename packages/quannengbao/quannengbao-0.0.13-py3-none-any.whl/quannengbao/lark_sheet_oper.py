from datetime import datetime
from time import sleep
import json
import threading

import lark_oapi as lark
import numpy as np
import pandas as pd

from quannengbao.data_oper import DataOperator
from quannengbao.image_process import ImageProcess as ip

import logging
import warnings

logging.basicConfig()
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class CellCal():

    @classmethod
    def cell_type_info(cls):
        cls.format_types = ["text", "mention_user", "mention_document", "value", "date_time", "checkbox", "file",
                            "image", "link", "reminder", "formula", "single_option", "multiple_option",
                            "date_validation", "datetime_option"]

    @staticmethod
    def number_to_letter(column_number):
        """
        Convert column number to Excel-style column letter.
        """
        letters = ''
        while column_number > 0:
            remainder = (column_number - 1) % 26
            letters = chr(ord('A') + remainder) + letters
            column_number = (column_number - 1) // 26
        return letters

    @staticmethod
    def letter_to_number(column_letter):
        """
        Convert Excel-style column letter to column number.
        """
        column_number = 0
        for char in column_letter:
            column_number = column_number * 26 + (ord(char) - ord('A') + 1)
        return column_number

    @classmethod
    def col_row_to_cell(cls, columns, rows):
        """
        Convert column number and row number to Excel-style cell reference.
        """
        cell = cls.number_to_letter(columns) + str(rows)
        return cell

    @classmethod
    def cell_to_col_row(cls, cell):
        """
        Convert Excel-style cell reference to column number and row number.
        Supports multiple letters representing columns.
        """
        letters = ""
        for char in cell:
            if char.isalpha():
                letters += char
            else:
                break
        column = cls.letter_to_number(letters)
        row = int(cell[len(letters):])
        return column, row

    @classmethod
    def range_calc(cls, start_cell=None, columns=None, rows=None, range=None):
        """
        Calculate the range of a sheet.
        """
        if start_cell is not None and (rows is None or columns is None):
            raise ValueError("If start_cell is provided, rows and columns must also be provided.")

        if range is not None and (start_cell is not None or rows is not None or columns is not None):
            raise ValueError("If range is provided, start_cell, rows, and columns must be empty.")

        if range is not None:
            start_cell, end_cell = range.split(':')
            start_col, start_row = cls.cell_to_col_row(start_cell)
            end_col, end_row = cls.cell_to_col_row(end_cell)
            rows = end_row - start_row + 1
            columns = end_col - start_col + 1
        else:
            start_col, start_row = cls.cell_to_col_row(start_cell)
            end_col = start_col + columns - 1
            end_row = start_row + rows - 1
            end_cell = cls.col_row_to_cell(columns=end_col, rows=end_row)
            range = start_cell + ':' + end_cell

        opt_dct = {"range": range, 'strat_cell': start_cell, 'end_cell': end_cell, 'row': rows, 'col': columns}

        return opt_dct

    @classmethod
    def cell_move(cls, start_cell, columns, rows):
        start_col, start_row = cls.cell_to_col_row(start_cell)
        end_col = start_col + columns
        end_row = start_row + rows
        end_cell = cls.col_row_to_cell(columns=end_col, rows=end_row)
        return end_cell

    @classmethod
    def muti_range_calc(cls, start_cell=None, columns=None, rows=None, range=None, row_limit=None):
        all_range = cls.range_calc(start_cell, columns, rows, range)
        if not row_limit:
            return {'all_range': all_range, 'ranges': [all_range]}
        else:
            range_list = []
            left_rows = all_range['row']
            while left_rows != 0:
                add_rows = min(left_rows, row_limit)
                range_list.append(cls.range_calc(start_cell, columns, add_rows))
                start_cell = cls.cell_move(start_cell, 0, add_rows)
                left_rows = left_rows - add_rows
            return {'all_range': all_range, 'ranges': range_list}

    @classmethod
    def set_cell_type(cls, element, cell_type, affected_text=None):

        format_types = ["text", "mention_user", "mention_document", "value", "date_time", "checkbox", "file",
                        "image", "link", "reminder", "formula", "single_option", "multiple_option",
                        "date_validation", "datetime_option"]

        if cell_type == 'text':
            element_opt = '''
                {
                    "text": "%s",
                    "segment_style": 
                    {
                            "style": 
                            {
                            "bold": false,
                            "italic": false,
                            "strike_through": false,
                            "underline": false,
                            "fore_color": "#000000",
                            "font_size": 10
                            },
                    "affected_text": "string"
                    }   
                }
            ''' % element

        elif cell_type == 'link':
            if not affected_text:
                affected_text = str(element)
            else:
                affected_text = str(affected_text)

            element_opt = '''
            {
                "text": "%s",
                "link": "%s",
                "segment_styles": 
                [
                    {
                        "style": {
                            "bold": false,
                            "italic": false,
                            "strike_through": false,
                            "underline": false,
                            "fore_color": "#4E83FD",
                            "font_size": 10
                        },
                        "affected_text": "%s"
                    }
                ]
            }
            ''' % (affected_text, element, affected_text)
        else:
            element_opt = '''
                            {
                                "text": "%s",
                                "segment_style": 
                                {
                                        "style": 
                                        {
                                        "bold": false,
                                        "italic": false,
                                        "strike_through": false,
                                        "underline": false,
                                        "fore_color": "#000000",
                                        "font_size": 10
                                        },
                                "affected_text": "string"
                                }   
                            }
                        ''' % element

        return element_opt


class LarkSheetOperator():
    def __init__(self, client, doc_token):
        self.sheet_title = None
        self.client = client
        self.doc_token = doc_token
        self.sheet_token = None
        self.sheet_lst = None
        self.sheet_id = None
        self.first_sheet_id = None
        self.range = None
        self.row_cnt = None
        self.column_cnt = None
        self.dop = DataOperator()

    def base_req(self, uri, body_data=None, way=None):
        if not way:
            way = lark.HttpMethod.GET
        elif way == 'GET':
            way = lark.HttpMethod.GET
        elif way == 'POST':
            way = lark.HttpMethod.POST
        elif way == 'PUT':
            way = lark.HttpMethod.PUT
        else:
            raise ValueError('Please input right way as str - GET/POST/PUT')

        req: lark.BaseRequest = (lark.BaseRequest.builder()
                                 .http_method(way)
                                 .token_types({lark.AccessTokenType.TENANT})
                                 .uri(uri)
                                 .body(body_data)
                                 .build())
        resp = self.client.request(req)

        if not resp.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, "
                f"code: {resp.code}, "
                f"msg: {resp.msg}, "
                f"log_id: {resp.get_log_id()}")
            logger.warning(resp.raw)
        return resp

    def get_spreadsheets_info(self):
        def do():
            resp = self.base_req(uri=f"/open-apis/sheets/v2/spreadsheets/{self.doc_token}/metainfo", way='GET')

            resp_json = json.loads(lark.JSON.marshal(resp, indent=4))
            resp_json_content = json.loads(resp_json.get('raw').get('content'))
            resp_json_content_data = resp_json_content.get('data')

            sheet_token = resp_json_content_data.get('spreadsheetToken')
            logger.info(f"sheet_token: {sheet_token}")
            resp_json_content_data_sheets = resp_json_content_data.get('sheets')
            sheets_lst = resp_json_content_data_sheets
            logger.debug(f"sheets_lst: {sheets_lst}")
            first_sheet_id = resp_json_content_data_sheets[0].get('sheetId')
            self.sheet_token = sheet_token
            self.doc_token = sheet_token
            self.sheet_lst = sheets_lst
            self.first_sheet_id = first_sheet_id
            return resp_json

        i = 0
        while i < 30:
            try:
                resp_json = do()
                return resp_json
            except Exception as e:
                i += 1
                print(f'读取sheet信息错误,将尝试第{i + 1}次 {e}')
                sleep(6)

    def select_first_sheet(self):
        self.get_spreadsheets_info()
        self.sheet_id = self.first_sheet_id
        return self.first_sheet_id

    def select_sheet(self, sheet_no=None, sheet_name=None):
        self.get_spreadsheets_info()

        if not sheet_no and not sheet_name:
            raise ValueError('Must specify either sheet_no or sheet_name.')
        elif sheet_no is not None and sheet_name is not None:
            raise ValueError('Can specify witch sheet you select. Please just select one.')
        elif sheet_no is not None:
            self.sheet_id = self.sheet_lst[sheet_no - 1].get('sheetId')
            self.sheet_title = self.sheet_lst[sheet_no - 1].get('title')
            self.column_cnt = self.sheet_lst[sheet_no - 1].get('columnCount')
            self.row_cnt = self.sheet_lst[sheet_no - 1].get('rowCount')
            self.range = CellCal.range_calc(start_cell="A1", columns=self.column_cnt, rows=self.row_cnt).get('range')
            logger.info(f"selected_sheet_id: {self.sheet_id} , range: {self.range}")
        elif sheet_name is not None:
            for item in self.sheet_lst:
                if item['title'] == sheet_name:
                    self.sheet_id = item['sheetId']
                    self.sheet_title = item['title']
                    self.column_cnt = item['columnCount']
                    self.row_cnt = item['rowCount']
                    self.range = CellCal.range_calc(start_cell="A1", columns=self.column_cnt, rows=self.row_cnt).get(
                        'range')
                    logger.info(f"selected_sheet_id: {self.sheet_id} , range: {self.range}")
                else:
                    pass
        return self.sheet_id

    def oper_sheet(self, oper_type=None, title=None, index=None, sheet_id=None, ):
        req_lst = [
            {
                "addSheet": {
                    "properties": {}
                }
            },
            {
                "copySheet": {
                    "source": {},
                    "destination": {}
                }
            },
            {
                "deleteSheet": {
                    "sheetId": sheet_id
                }
            }
        ]
        req_dct = {}
        if oper_type == 'create':
            req_dct = req_lst[0]
            if sheet_id:
                raise ValueError('No need to specify sheet_id while using create')
            if not title:
                title = "NewSheet_" + datetime.now().strftime('%Y%m%d%H%M%S')
                logger.debug(f'未输入新建工作表名称 自动创建{title}')
            req_dct['addSheet']['properties']['title'] = title
            if index:
                req_dct['addSheet']['properties']['index'] = index
            logger.debug(f'工作表创建参数 title {title} 位置 {index}')

        elif oper_type == 'copy':
            req_dct = req_lst[2]
            if index is not None:
                raise ValueError('No need to specify index while using copy')
            if not sheet_id:
                sheet_id = self.sheet_id
                logger.debug(f'未输入工作表ID 使用预设 {sheet_id}')
            req_dct['copySheet']['source']['sheetId'] = sheet_id
            if not title:
                raise ValueError('Must specify title')
            req_dct['copySheet']['destination']['title'] = title
            logger.debug(f'工作表复制参数 sheet_id {sheet_id} title {title}')

        elif oper_type == 'delete':
            req_dct = req_lst[2]
            if title is not None and sheet_id is not None:
                raise ValueError('Must not specify both sheet_id and title')
            if index:
                raise ValueError('No need to specify title/index while using delete')

            if title:
                self.select_sheet(sheet_name=title)
            if not sheet_id:
                sheet_id = self.sheet_id
                logger.debug(f'未输入工作表ID 使用预设 {sheet_id}')
            req_dct['deleteSheet']['sheetId'] = sheet_id
            logger.debug(f'工作表删除参数 sheet_id {sheet_id}')

        else:
            raise ValueError('Unknown oper_type')
        body_data = {"requests": [req_dct]}
        logger.debug(body_data)
        resp = self.base_req(
            uri=f"/open-apis/sheets/v2/spreadsheets/{self.doc_token}/sheets_batch_update",
            body_data=body_data, way='POST')
        self.select_sheet(sheet_name=title)
        return resp.raw.content

    def update_sheet(self, sheet_id: str = None, title: str = None, index: int = None, hidden: bool = False,
                     frozen_rt: int = 0, frozen_cc: int = 0, ):
        '''
        更新工作表属性，包含命名表/改顺序/隐藏/冻结行列
        :param sheet_id:
        :param title:
        :param index:
        :param hidden:
        :param frozen_rt:
        :param frozen_cc:
        :return:
        '''
        if not sheet_id:
            sheet_id = self.sheet_id

        body_data = {
            "requests": [
                {
                    "updateSheet": {
                        "properties": {}
                    }
                }
            ]
        }

        body_data['requests'][0]['updateSheet']['properties']['sheetId'] = self.sheet_id
        body_data['requests'][0]['updateSheet']['properties']['hidden'] = hidden
        if title:
            body_data['requests'][0]['updateSheet']['properties']['title'] = title
        if index:
            body_data['requests'][0]['updateSheet']['properties']['index'] = index
        if frozen_cc:
            body_data['requests'][0]['updateSheet']['properties']['frozenColCount'] = frozen_cc
        if frozen_rt:
            body_data['requests'][0]['updateSheet']['properties']['frozenRowCount'] = frozen_rt

        resp = self.base_req(uri=f"/open-apis/sheets/v2/spreadsheets/{self.doc_token}/sheets_batch_update",
                             body_data=body_data, way='POST')
        logger.debug(resp)
        return resp

    def write_range_data(self, data, range):
        body_data = {
            "valueRange": {
                "range": self.sheet_id + "!" + range,
                "values": data
            }
        }

        req: lark.BaseRequest = (lark.BaseRequest.builder()
                                 .http_method(lark.HttpMethod.PUT)
                                 .token_types({lark.AccessTokenType.TENANT})
                                 .uri(f"/open-apis/sheets/v2/spreadsheets/{self.doc_token}/values")
                                 .body(body_data)
                                 .build())
        resp = self.client.request(req)
        logger.debug(f'write_range_data {range}')
        if not resp.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, "
                f"code: {resp.code}, "
                f"msg: {resp.msg}, "
                f"log_id: {resp.get_log_id()}")
            logger.warning(f'单元格{range},写入失败 {resp.msg}')

    def write_df_to_sheet(self, df: pd.DataFrame, start_cell, header=False, row_limit=None, to_convert=True,
                          not_convert_lst: list = None):
        if to_convert:
            if not_convert_lst:
                # 保存原始列顺序
                original_order = df.columns.tolist()
                # 不转换列
                exclude_cols = not_convert_lst
                # 对不需要转换的列和需要转换的列分组
                not_convert = df[exclude_cols]
                to_convert = df.drop(columns=exclude_cols).replace(
                    {np.inf: '', -np.inf: '', pd.NaT: None, np.nan: '', '': '', 'NULL': '',
                     'null': ''})
                # 仅对需要转换的列执行转换函数
                converted = to_convert.applymap(lambda x: self.dop.convert_text_to_number(x))
                # 按照原始顺序拼接数据
                df = pd.concat([converted, not_convert], axis=1)[original_order]
            else:
                df = df.replace({np.inf: '', -np.inf: '', pd.NaT: None, np.nan: '', '': '', 'NULL': '',
                                 'null': ''}).applymap(lambda x: self.dop.convert_text_to_number(x))
                df = df.applymap(lambda x: self.dop.convert_datetime_to_str(x))

        def write_batch(_df, _start_cell):
            logger.info(f'写入起始单元格 {_start_cell}')
            sleep(0.5)
            dfo = DataOperator()
            data_lst = dfo.muti_data_lst_calc(_df, row_limit, header=header)
            data_lst_all = dfo.muti_data_lst_calc(_df, header=header)
            columns = len(data_lst_all[0][0])
            rows = len(data_lst_all[0])

            if not row_limit:
                data_lst_cal = data_lst_all
            else:
                data_lst_cal = data_lst

            range_lst = CellCal.muti_range_calc(start_cell=_start_cell, columns=columns, rows=rows, row_limit=row_limit)
            for data, rng in zip(data_lst_cal, range_lst['ranges']):
                self.write_range_data(data, rng['range'])

        max_col_per_batch = 50
        col_max_n = len(list(df.columns))
        round_num = col_max_n // max_col_per_batch + 1
        st_cell = start_cell
        col_start_n = 0
        for i in range(round_num):
            round_n = i + 1
            col_end_n = min(max_col_per_batch * round_n, col_max_n)
            df_ins = df.iloc[:, col_start_n:col_end_n]
            write_batch(_df=df_ins, _start_cell=st_cell)
            col_move_n = col_end_n - col_start_n
            col_start_n = col_end_n
            st_cell = CellCal.cell_move(st_cell, columns=col_move_n, rows=0)
            sleep(0.3)

    def clear_sheet_data(self, sheet_id=None, range=None):
        if not sheet_id:
            sheet_id = self.sheet_id
        if not range:
            range = self.range
        rng = sheet_id + "!" + range

        json_str = f'''{{"ranges":["{rng}"]}}'''
        body = json.loads(json_str)
        request: lark.BaseRequest = lark.BaseRequest.builder() \
            .http_method(lark.HttpMethod.POST) \
            .uri(f"/open-apis/sheets/v3/spreadsheets/{self.doc_token}/sheets/{sheet_id}/values/batch_clear") \
            .token_types({lark.AccessTokenType.TENANT}) \
            .body(body) \
            .build()

        # 发起请求
        response: lark.BaseResponse = self.client.request(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.request failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
            return

        # 处理业务结果
        lark.logger.info(str(response.raw.content, lark.UTF_8))
        logger.debug(f"清除: {rng}")
        return response

    def read_sheet(self, sheet_id=None, range=None):
        if not sheet_id:
            sheet_id = self.sheet_id
        if not range:
            range = self.range
        rng = sheet_id + "!" + range

        request: lark.BaseRequest = lark.BaseRequest.builder() \
            .http_method(lark.HttpMethod.GET) \
            .uri(
            f"/open-apis/sheets/v2/spreadsheets/{self.doc_token}/values/{rng}?valueRenderOption=FormattedValue"
            f"&dateTimeRenderOption=FormattedString") \
            .token_types({lark.AccessTokenType.TENANT}) \
            .build()

        # 发起请求
        response: lark.BaseResponse = self.client.request(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.request failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
            return

        # 处理业务结果
        lark.logger.info(str(response.raw.content, lark.UTF_8))
        str_json = lark.JSON.marshal(response.raw.content, indent=4)
        values: list[list] = json.loads(json.loads(str_json)).get('data').get('valueRange').get('values')
        logger.debug(f"表格读取完成! 读取范围: {rng}")
        return values

    def write_image(self, image_binary, sheet_id=None, cell=None, client=None):
        if not sheet_id:
            sheet_id = self.sheet_id
        if not cell:
            cell = 'A1'
        if not client:
            client = self.client

        body_data = {
            "range": sheet_id + "!" + cell + ":" + cell,
            "image": image_binary,
            "name": "test.png"
        }

        req: lark.BaseRequest = (lark.BaseRequest.builder()
                                 .http_method(lark.HttpMethod.POST)
                                 .token_types({lark.AccessTokenType.TENANT})
                                 .uri(f"/open-apis/sheets/v2/spreadsheets/{self.doc_token}/values_image")
                                 .body(body_data)
                                 .build())
        resp = client.request(req)

        if not resp.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, "
                f"code: {resp.code}, "
                f"msg: {resp.msg}, "
                f"log_id: {resp.get_log_id()}")
        logger.debug(f"图片写入完成! 写入单元格: {cell}")
        return resp

    def col_write_image(self, lst_w_image: list, start_cell, header=True):
        if header:
            cell = CellCal.cell_move(start_cell=start_cell, columns=0, rows=1)
        else:
            cell = start_cell
        for image in lst_w_image:
            if image:
                self.write_image(image_binary=image, cell=cell)
            else:
                pass
            cell = CellCal.cell_move(start_cell=cell, columns=0, rows=1)

    def cell_fetch_write_image(self, image_url, sheet_id=None, cell=None, client=None):
        if not sheet_id:
            sheet_id = self.sheet_id
        if not cell:
            cell = 'A1'
        if not client:
            client = self.client

        image_binary = ip().get_image_binary(image_url)
        resp = self.write_image(image_binary, sheet_id=sheet_id, cell=cell, client=client)
        return resp

    def cell_fetch_write_image_from_col(self, col, start_cell, scale_px=None, threads_num=1, client_lst=None):
        # 获取整列url列表
        url_lst = []
        for row_item in col:
            try:
                url = row_item[0][0]["text"]
            except Exception as e:
                try:
                    url = row_item[0]
                except Exception as e:
                    url = ""

            url_lst.append(url)

        # 按照线程数量拆分列表
        item_cnt = len(url_lst)
        cnt_per_batch = item_cnt // threads_num
        url_dct = {}
        for i in range(threads_num):
            if i == threads_num - 1:
                lst = url_lst[i * cnt_per_batch:item_cnt - 1]
            else:
                lst = url_lst[i * cnt_per_batch:(i + 1) * cnt_per_batch - 1]
            url_dct[start_cell] = lst
            start_cell = CellCal.cell_move(start_cell, 0, cnt_per_batch)

        def _lst_fetch_write_image(_cell, _url_lst, _scale_px):
            for url in _url_lst:
                logger.debug(url)
                if not _scale_px:
                    pass
                else:
                    url = url.replace("200:200", "1200:1200")
                if threads_num == 1:
                    clent = self.client
                else:
                    raise ValueError('目前仅支持一个线程')
                self.cell_fetch_write_image(url, cell=_cell, client=clent)
                _cell = CellCal.cell_move(_cell, 0, 1)

        thread_lst = []
        for k, v in url_dct.items():
            thread = threading.Thread(target=_lst_fetch_write_image, args=(k, v, scale_px))
            thread_lst.append(thread)
        for thread in thread_lst:
            thread.start()
        for thread in thread_lst:
            thread.join()

    def set_range_fromate(self, range, font_bold="false", font_italic="ture", font_fontSize="10pt/1.5",
                          font_clean="false", textDecoration=0, formatter="", hAlign=0, vAlign=0,
                          foreColor="#000000", backColor="#21d11f", borderType="FULL_BORDER", borderColor="#ff0000",
                          clean="false"):
        '''
        :param range: string	必须	查询范围，包含 sheetId 与单元格范围两部分，目前支持四种索引方式，详见在线表格开发指南
        :param font_bold: 非必须	是否加粗
        :param font_italic: 非必须	是否斜体
        :param font_fontSize: 非必须	字体大小 字号大小为9~36 行距固定为1.5，如:10pt/1.5
        :param font_clean: 非必须	清除 font 格式,默认 false
        :param textDecoration: 非必须	文本装饰 ，0 默认，1 下划线，2 删除线 ，3 下划线和删除线
        :param formatter: 非必须	数字格式，详见附录 sheet支持数字格式类型
        :param hAlign: 非必须	水平对齐，0 左对齐，1 中对齐，2 右对齐
        :param vAlign: 非必须	垂直对齐， 0 上对齐，1 中对齐， 2 下对齐
        :param foreColor: string	非必须	字体颜色
        :param backColor: string	非必须	背景颜色
        :param borderType: 非必须	边框类型，可选 "FULL_BORDER"，"OUTER_BORDER"，"INNER_BORDER"，"NO_BORDER"，"LEFT_BORDER"，"RIGHT_BORDER"，"TOP_BORDER"，"BOTTOM_BORDER"
        :param borderColor: 非必须	边框颜色
        :param clean: 非必须	是否清除所有格式,默认 false
        :return:
'''
        format_dct_str = \
            '''
    {
          "appendStyle":
        { 
             "range": %s,
             "style":{
                  "font":
                  {
                      "bold":%s,
                      "italic":%s,
                      "fontSize":%s,
                      "clean":%s  
                  },    
                  "textDecoration":%s,
                  "formatter":%s,
                  "hAlign": %s, 
                  "vAlign":%s,   
                  "foreColor":%s,
                  "backColor":%s,
                  "borderType":%s,
                  "borderColor": %s,
                  "clean": %s 
                  }
        }
    }
    ''' % (range, font_bold, font_italic, font_fontSize, font_clean, textDecoration, formatter, hAlign, vAlign,
           foreColor, backColor, borderType, borderColor, clean)

        req: lark.BaseRequest = (lark.BaseRequest.builder()
                                 .http_method(lark.HttpMethod.POST)
                                 .token_types({lark.AccessTokenType.TENANT})
                                 .uri(f"/open-apis/sheets/v2/spreadsheets/{self.doc_token}/style")
                                 .body(format_dct_str)
                                 .build())
        resp = self.client.request(req)

        if not resp.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, "
                f"code: {resp.code}, "
                f"msg: {resp.msg}, "
                f"log_id: {resp.get_log_id()}")
        return resp

    def set(self, sheet_id=None, axis=1, startIndex=1, endIndex=1, visible="true", fixedSize=15):
        '''

        :param sheet_id: 默认 self.sheet_id
        :param axis: 非必须	默认 1 ROWS ，可选 1 ROWS、2 COLUMNS
        :param startIndex: 必须	开始的位置
        :param endIndex: 必须	结束的位置
        :param visible: 非必须	true 为显示，false 为隐藏行列
        :param fixedSize: 非必须	行/列的大小
        :return:
        '''

        if not sheet_id:
            sheet_id = self.sheet_id
        if axis == 1:
            dimens = "ROWS"
        elif axis == 0:
            dimens = "COLUMNS"
        else:
            raise ValueError("Invalid axis ,please text 0/1")

        format_dct_str = ''' 
         {
            "dimension": {
                "sheetId": %s,
                "majorDimension": %s,
                "startIndex": %s,
                "endIndex": %s
            },
            "dimensionProperties": {
                "visible": %s,
                "fixedSize": %s
            }
        }        
        ''' % (sheet_id, dimens, startIndex, endIndex, visible, fixedSize)

        req: lark.BaseRequest = (lark.BaseRequest.builder()
                                 .http_method(lark.HttpMethod.POST)
                                 .token_types({lark.AccessTokenType.TENANT})
                                 .uri(f"/open-apis/sheets/v2/spreadsheets/{self.doc_token}/style")
                                 .body(format_dct_str)
                                 .build())
        resp = self.client.request(req)

        if not resp.success():
            lark.logger.error(
                f"client.im.v1.message.create failed, "
                f"code: {resp.code}, "
                f"msg: {resp.msg}, "
                f"log_id: {resp.get_log_id()}")
        return resp
