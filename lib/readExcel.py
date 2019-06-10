# coding:utf-8
import xlrd, os, json, logging

log = logging.getLogger('log')  # 初始化log


class ExcelUtil:
    def __init__(self, excel_path, sheet_name="Sheet1"):
        self.data = xlrd.open_workbook(excel_path)
        self.table = self.data.sheet_by_name(sheet_name)
        self.keys = self.table.row_values(0)  # 获取第一行作为key值
        self.rowNum = self.table.nrows  # 获取总行数
        self.colNum = self.table.ncols  # 获取总列数

    def dict_data(self, make=True):
        if self.rowNum <= 1:
            log.error("总行数小于1")
        else:
            r = []
            j = 1
            if make:
                for i in list(range(self.rowNum - 1)):  # 去掉行首 self.rowNum - 1
                    s = {'rowNum': i + 2}
                    values = self.table.row_values(j)  # 从第二行取对应values值
                    for x in list(range(self.colNum)):
                        s[self.keys[x]] = values[x]
                    r.append(s)
                    j += 1
                return r  # 返回list包含的dict数据
            else:
                for i in list(range(self.rowNum - 1)):  # 去掉行首 self.rowNum - 1
                    s = {}
                    values = self.table.row_values(j)  # 从第二行取对应values值
                    s[self.keys[1]] = values[1]
                    r.append(s)
                    j += 1
                return r  # 返回list包含的dict数据


def get_json(path, field=''):
    """获取json文件中的值"""
    with open(path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        if field:
            data = json_data.get(field)
            return data
        else:
            return json_data


if __name__ == "__main__":
    excel_path = os.path.abspath(
        os.path.dirname(os.path.dirname(
            __file__))) + '\\static' + '\\data' + '\\excel' + '\\demo_api_3.xlsx'  # case excel file path
    sheetName = "Sheet2"
    data = ExcelUtil(excel_path, sheetName)
    print(data.dict_data(make=False))
