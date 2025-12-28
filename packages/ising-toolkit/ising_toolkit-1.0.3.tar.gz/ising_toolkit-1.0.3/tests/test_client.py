import unittest
from unittest.mock import Mock, patch
from ising.client import IsingClient, IsingClientError


class TestIsingClient(unittest.TestCase):

    def setUp(self):
        self.api_key = "341e46328ace46ceaeb48bcc47313fb8"
        self.client = IsingClient(api_key=self.api_key)

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.client.api_key, self.api_key)

    @patch('ising.client.requests.Session.request')
    def test_get_task_success(self, mock_request):
        """测试 get_task 成功情况"""
        # 准备模拟响应
        mock_response = Mock()
        mock_response.json.return_value = {"task_id": "251027103828465", "status": "completed"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        # 调用方法
        result = self.client.get_task("251027103828465")

        # 验证结果
        self.assertEqual(result, {"task_id": "251027103828465", "status": "completed"})
        mock_request.assert_called_once_with('GET', 'http://open-staging.isingq.com/v1/tasks/251027103828465', headers={'Authorization': self.api_key})




if __name__ == '__main__':
    unittest.main()