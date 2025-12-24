from enum import Enum

'''
价格枚举
'''


class CookieEnum(Enum):
    THS_COOKIE = ('ths_cookie', '同花顺cookie')
    EM_COOKIE = ('em_cookie', '东方财富cookie')
    XUE_QIU_COOKIE = ('xue_qiu_cookie', '雪球cookie')

    def __init__(self, cookie_code, cookie_name):
        self.cookie_code = cookie_code
        self.cookie_name = cookie_name
