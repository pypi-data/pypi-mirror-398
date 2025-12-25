class AwesomeWeatherClient:
    """一个用于查询天气的客户端。"""

    def __init__(self, api_key: str, base_url: str = "https://api.weather.example.com"):
        self.api_key = api_key
        self.base_url = base_url

    def get_current_weather(self, location: str, unit: str = "celsius") -> dict:
        print("Hello World")
        return {"message": "方法调用成功", "location": location}