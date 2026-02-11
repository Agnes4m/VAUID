async def time_delta(m_time: float) -> str:
    hours, remainder = divmod(m_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}小时{minutes}分钟{seconds}秒"
