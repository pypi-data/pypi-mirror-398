class TemplateTaskCreateRequest:
    """
    Request class for creating template tasks.
    """

    def __init__(self, templateId=None, name=None, computerTypeId=None, payload=None):
        """
        Initialize TemplateTaskCreateRequest with specified parameters.
        
        :param templateId: Integer - template id
        :param name: Str - task name
        :param computerTypeId: Integer - computer type id
        :param payload: Str - payload data
        """
        self.templateId = templateId
        self.name = name
        self.computerTypeId = computerTypeId
        self.payload = payload

    def to_dict(self):
        """
        Convert the request object to dictionary for API request.
        
        :return: Dictionary representation of the request object
        """
        return {
            "templateId": self.templateId,
            "name": self.name,
            "computerTypeId": self.computerTypeId,
            "payload": self.payload
        }

    def from_dict(self, data):
        """
        Populate the request object from dictionary.
        
        :param data: Dictionary containing the request data
        """
        self.templateId = data.get("templateId")
        self.name = data.get("name")
        self.computerTypeId = data.get("computerTypeId")
        self.payload = data.get("payload")