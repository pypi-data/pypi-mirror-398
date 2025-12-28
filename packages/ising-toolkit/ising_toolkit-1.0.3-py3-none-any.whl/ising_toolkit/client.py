import requests


class IsingClientError(Exception):
    """Ising SDK 异常类"""
    pass


class AuthenticationError(IsingClientError):
    """认证错误异常类"""
    pass


class IsingClient:
    def __init__(self, api_key=None, base_url="https://api.isingq.com"):
        """
        初始化SDK客户端

        :param api_key: 认证密钥
        :param base_url: API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()

    def _request(self, method, endpoint, **kwargs):
        """内部请求方法"""
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.get('headers', {})
        headers['Authorization'] = self.api_key
        headers['channel'] = "sdk"
        kwargs['headers'] = headers

        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed: Invalid API key")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise IsingClientError(f"API request failed: {str(e)}")

    def get_task(self, task_id):
        """获取资源"""
        return self._request('GET', f'tasks/{task_id}')

    def get_task_list(self, page_no=1, page_size=10):
        """
        获取任务列表

        :param page_no: 页码
        :param page_size: 每页数量
        :return: API响应数据
        """
        return self._request('POST', 'tasks/list', json={'page_no': page_no, 'page_size': page_size})


    def create_general_task(self, request):
        """
        创建通用任务
        
        :param request: GeneralTaskCreateRequest 对象
        :return: API响应数据
        """
        return self._request('POST', 'tasks/create-general', json=request.to_dict())


    def create_template_task(self, request):
        """
        创建模板任务

        :param request: TemplateTaskCreateRequest 对象
        :return: API响应数据
        """
        return self._request('POST', 'tasks/create-template', json=request.to_dict())