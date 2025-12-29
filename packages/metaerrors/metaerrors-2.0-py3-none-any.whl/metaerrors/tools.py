"""Small, frequently used functions"""

def double_quotes(string: str) -> str:
    return '\"%s\"' % string

def quotes(string: str) -> str:
    return "\'%s\'" % string

dq = double_quotes #Synonym
q = quotes #Synonym

def frmt_msg(err: BaseException, frmt: str) -> str:
    return frmt.format(msg=err.__str__(), name=err.__class__.__name__)
