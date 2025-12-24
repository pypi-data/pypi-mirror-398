from enum import Enum


class BlackClassify(Enum):
    # 一 交易类
    TRANSACTIONS = (1, '交易类', 'transactions', 1, 'transactions', '交易类')
    # 成交量
    AMOUNT_RISK = (1, '交易类', 'transactions', 2, 'amount_risk', '成交量风险')
    # 股东数量风险
    SHAREHOLDERS_NUMBER_RISK = (1, '交易类', 'transactions', 2, 'shareholders_number_risk', '股东数量风险')
    # 市值
    MV_RISK = (1, '交易类', 'transactions', 2, 'mv_risk', '市值风险')
    # 收盘价问题
    CLOSE_PRICE_RISK = (1, '交易类', 'transactions', 2, 'close_price_risk', '收盘价风险')

    # 二 财务类
    FINANCIAL = (1, '财务类', 'financial', 1, 'financial', '财务类')
    # 利润表+营业收入 净利润为负且营收低于1亿-最近一个会计年度经审计的净利润为负目营业收入低于1亿元，或追溯重述后最近一个会计年度净利润为负且营业收入低于!亿元
    FINANCIAL_PROBLEM_PROFIT = (1, '财务类', 'financial', 2, 'financial_problem_profit', '利润表+营业收入风险')
    # 净资产为负数,高杠杆-最近一个会计年度经审计的期未净资产为负，或追溯重述后最近，个会计年度期末净资产为负
    FINANCIAL_PROBLEM_DEBT = (1, '财务类', 'financial', 2, 'financial_problem_debt', '净资产风险')
    # 财务年报审计有问题(非标准无保留)-最近一个会计年度的财务会计报告被出具无法表示意见或否定意见的审计报告
    AUDIT_PROBLEM = (1, '财务类', 'financial', 2, 'audit_problem', '年报审计问题')
    # 财务造假 -中国证监会行政处罚决定表明公司己披露的最近一个会计年度财务报告存在虚假记载、误导性陈述或者重大遗漏，导致该年度相关则务指标实际已触及本款第一项、第一项情形
    FINANCIAL_FRAUD = (1, '财务类', 'financial', 2, ' financial_fraud', '财务造假')

    # 三 规范类
    COMPLIANCE = (1, '规范类', 'compliance', 1, 'compliance', '规范类')
    # 未在法定期限内披露年度报告或者半年度报告，且在公司股票停牌两个月内仍未披露
    UNDISCLOSED_REPORT = (1, '规范类', 'compliance', 2, 'undisclosed_report', '未披露财务报告')
    # 报告不保证真实准确完整 -半数以上董事无法保证年度报告或者半年度报告真实、准
    # 确、完整，且在公司股票停牌两个月内仍有半数以上董事无法保证的
    REPORT_NOT_TRUE_COMPLETE = (1, '规范类', 'compliance', 2, 'report_not_true_complete', '报告不保证真实准确完整')
    # 信息披露缺陷
    REPORT_DISCLOSED_DEFECT = (1, '规范类', 'compliance', 2, 'report_disclosure_defect', '信息披露缺陷')

    # 四 重大违法类
    MAJOR_VIOLATIONS = (1, '重大违法类', 'major_violations', 2, 'major_violations', '重大违法类')
    # 重大违法类-立案调查-损害证券市场秩序
    REGISTER_INVESTIGATE = (1, '重大违法类', 'major_violations', 2, 'register_investigate', '立案调查')
    # 重大违法类-危害安全-损害国家利益，社会公众利益
    ENDANGER_SAFETY = (1, '重大违法类', 'major_violations', 2, 'endanger_safety', '危害安全')

    # 五 自主拉黑
    SELF_SHIELD = (1, '自主拉黑', 'self_shield', 1, 'self_shield', '自主拉黑')
    # 自主拉黑—庄股
    CONTROLLED_STOCK = (1, '自主拉黑', 'self_shield', 2, 'controlled_stock', '庄股')
    # 自主拉黑—其他
    SELF_SHIELD_OTHER = (1, '自主拉黑', 'self_shield', 2, 'self_shield_other', '其他原因')

    # up_level 上一个层级  level 当前层级
    def __init__(self, up_level, up_level_name, up_level_code, level, level_code, level_name):
        self.up_level = up_level
        self.up_level_code = up_level_code
        self.up_level_name = up_level_name
        self.level = level
        self.level_name = level_name
        self.level_code = level_code
