from lagent.tools.registry import tool

@tool
def get_weather(city: str) -> str:
    """
    Get weather for a specific city.
    
    Args:
        city: The name of the city.
    """
    return "12 月 15 日天气晴朗，温度 12 摄氏度，空气质量优"

@tool
def multiply(a: int, b: int) -> int:
    """
    Multiply two integers.
    
    Args:
        a: The multiplier.
        b: The multiplicand.
    """
    return a * b
