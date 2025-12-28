import json
from .client import IsingClient, IsingClientError, AuthenticationError
from .request import GeneralTaskCreateRequest, TemplateTaskCreateRequest

class IsingSolver:
    """
    一个高级封装类 (Facade)，用于简化 Ising 任务的提交和管理。
    用户只需在初始化时提供 API 密钥。
    """

    def __init__(self, api_key, base_url=None):
        """
        初始化 IsingSolver 客户端。

        :param api_key: 您的 API 密钥 (只需提供一次)
        :param base_url: (可选) API 基础 URL。如果为 None，将使用 client 中的默认值
        """
        client_args = {'api_key': api_key}
        if base_url:
            # 参考 ising/client.py，默认 URL 是 "https://api.isingq.com"
            client_args['base_url'] = base_url
        
        # 实例化并持有一个低级客户端
        # 这个 client 实例保存了 api_key
        self._client = IsingClient(**client_args)

    def solve(self, J, h, name="Ising SDK Task", computerTypeId=None, 
                      type="spin", shots=None, postProcess=None):
        """
        提交一个通用的 Ising 任务。
        用户只需传入矩阵数据，API 密钥会自动使用。

        :param J: J 矩阵 (例如: list of lists 或 numpy array)。
                         将被序列化为 JSON 字符串。
        :param h: H 矩阵 (例如: list 或 numpy array)。
                         将被序列化为 JSON 字符串。
        :param name: (可选) 任务名称
        :param computerTypeId: (可选) 计算机类型 ID
        :param typ: (可选) 问题类型，默认 "spin"
        :param shots: (可选) 计算次数，默认 1000
        :param postProcess: (可选) 后处理
        :return: API 响应数据
        """
        try:
            # 1. 矩阵处理 (序列化为 JSON 字符串)
            J_str = json.dumps(J)
            h_str = json.dumps(h)

            # 2. 自动创建请求对象
            request = GeneralTaskCreateRequest(
                name=name,
                computerTypeId=computerTypeId,
                inputJFile=J_str,
                inputHFile=h_str,
                questionType=type,
                caculateCount=shots,
                postProcess=postProcess
            )

            # 3. 使用持有的 client 实例调用方法
            # (基于 ising/client.py 中的 create_general_task)
            return self._client.create_general_task(request)

        except (IsingClientError, AuthenticationError) as e:
            raise e
        except json.JSONDecodeError as e:
            raise IsingClientError(f"矩阵序列化失败: {str(e)}")
        except Exception as e:
            raise IsingClientError(f"封装函数执行出错: {str(e)}")

    def solve_template(self, templateId, payload, name="Ising SDK Task", computerTypeId=None):
        """
        提交一个模板 Ising 任务。
        API 密钥会自动使用。

        :param templateId: 模板 ID
        :param payload: 模板所需的数据 (例如: dict)，将被序列化为 JSON 字符串
        :param name: (可选) 任务名称
        :param computerTypeId: (可选) 计算机类型 ID
        :return: API 响应数据
        """
        try:
            # 1. 序列化 payload
            payload_str = json.dumps(payload)

            # 2. 创建请求对象
            # (基于 ising/request/TemplateTaskCreateRequest.py)
            request = TemplateTaskCreateRequest(
                templateId=templateId,
                name=name,
                computerTypeId=computerTypeId,
                payload=payload_str
            )
            
            # 3. 使用持有的 client 实例调用方法
            # (基于 ising/client.py 中的 create_template_task)
            return self._client.create_template_task(request)

        except (IsingClientError, AuthenticationError) as e:
            raise e
        except json.JSONDecodeError as e:
            raise IsingClientError(f"Payload 序列化失败: {str(e)}")
        except Exception as e:
            raise IsingClientError(f"封装函数执行出错: {str(e)}")

    def get_task(self, task_id):
        """
        获取任务详情。
        (封装底层 client 的同名方法)
        """
        # (基于 ising/client.py 中的 get_task)
        return self._client.get_task(task_id)

    def get_task_list(self, page_no=1, page_size=10):
        """
        获取任务列表。
        (封装底层 client 的同名方法)
        """
        # (基于 ising/client.py 中的 get_task_list)
        return self._client.get_task_list(page_no, page_size)