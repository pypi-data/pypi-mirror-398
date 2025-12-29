from enum import Enum


class TerminalEnum(Enum):
    EASY_TRADER = ('easy_trader', 'easy_trader')
    QMT = ('qmt', 'qmt')

    def __init__(self, terminal_code, terminal_name):
        self.terminal_code = terminal_code
        self.terminal_name = terminal_name
