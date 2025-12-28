from jkexcel.app.application import ExcelApplication
import pyotp

if __name__ == '__main__':
    # wb = load_workbook('C:/Users/admin/Downloads/数据概览_数据概览报表_2025-12-25 11_16_58.xlsx')
    # ws = wb.active
    # wb.remove(ws)
    # wb.save('C:/Users/admin/Downloads/数据概览_数据概览报表_2025-12-25 11_16_58.xlsx')
    # app = ExcelApplication()
    # # 常用操作：显示窗口+禁用弹窗
    # wb = app.open_workbook(r"C:/Users/admin/Downloads/数据概览_数据概览报表_2025-12-25 16_53_24.xlsx")
    # wb.sheet(1).delete()
    # wb.save()
    # app.close()
    key = '7TCQOHYH5DOLEH5M7F2PSRMQ7GTJU36L'
    totp = pyotp.TOTP(key)
    print(totp.now())
    'pypi-AgEIcHlwaS5vcmcCJGU2NWYyOWI2LTNkNTAtNDRlYS1hY2FiLTliYWNjNGYyNTljNgACKlszLCI2ZjU0OWVkZC0yMjdlLTQxZGItYjMwMi00NGFkNjg3ZGQ2NWYiXQAABiCsYk0KJlQGOxBDmVBhOj5o0GLuTs4RAnnabNs7WJyjIg'