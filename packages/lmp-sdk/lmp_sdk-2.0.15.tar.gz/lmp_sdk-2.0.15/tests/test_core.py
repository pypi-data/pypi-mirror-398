import unittest
from unittest.mock import Mock, patch
from lmp_sdk.my_awesome_sdk.core import AwesomeWeatherClient

class TestAwesomeWeatherClient(unittest.TestCase):

    @patch('src.lmp.core.APIClient') # 模拟APIClient类
    def test_get_current_weather(self, mock_api_client):
        # 准备模拟数据
        mock_response = {"temperature": 22, "condition": "Sunny"}
        mock_instance = mock_api_client.return_value
        mock_instance.get.return_value = mock_response

        # 创建客户端并调用方法
        client = AwesomeWeatherClient(api_key="fake_key")
        result = client.get_current_weather("Beijing")

        # 断言行为符合预期
        mock_instance.get.assert_called_once_with("v1/current", params={"location": "Beijing"})
        self.assertEqual(result, mock_response)