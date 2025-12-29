from datetime import datetime
from zoneinfo import ZoneInfo

def format_datetime(time_str: str) -> str:
    """
    将 ISO 格式的时间字符串转换为东八区时间
    """
    if not time_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        dt_utc = dt.replace(tzinfo=ZoneInfo("UTC"))
        dt_cst = dt_utc.astimezone(ZoneInfo("Asia/Shanghai"))
        return dt_cst.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return time_str

