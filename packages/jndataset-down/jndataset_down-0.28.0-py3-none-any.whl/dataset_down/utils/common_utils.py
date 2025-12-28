import re

def is_email(email_str):
    """
    判断一个字符串是否是有效的邮箱地址
    
    Args:
        email_str (str): 待检测的字符串
        
    Returns:
        bool: 如果是有效邮箱地址返回True,否则返回False
    """
    # 邮箱正则表达式模式
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # 使用正则表达式匹配
    if re.match(pattern, email_str):
        return True
    else:
        return False


def is_chinese_phone(phone_str):
    """
    判断一个字符串是否是手机号码
    
    Args:
        phone_str (str): 待检测的字符串
        
    Returns:
        bool: 如果是手机号码返回True,否则返回False
    """
    # 手机号码正则表达式模式
    pattern = r'^1[3-9]\d{9}$'
    
    # 使用正则表达式匹配
    if re.match(pattern, phone_str):
        return True
    else:
        return False
    
def is_all_digits(str):
    """
    判断一个字符串是否只包含数字
    
    Args:
        str (str): 待检测的字符串
        
    Returns:
        bool: 如果只包含数字返回True,否则返回False
    """
    # 使用正则表达式匹配
    if re.match(r'^\d+$', str):
        return True
    else:
        return False

