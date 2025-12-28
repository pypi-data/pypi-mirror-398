class GeneralTaskCreateRequest:
    """
    Request class for creating general tasks.
    """

    def __init__(self, name=None, computerTypeId=None, inputJFile=None, inputHFile=None, 
                 questionType=None, caculateCount=None, postProcess=None):
        """
        Initialize GeneralTaskCreateRequest with specified parameters.
        
        :param name: Str - task name
        :param computerTypeId: Integer - computer type id
        :param inputJFile: Str - input J file
        :param inputHFile: Str - input H file
        :param questionType: Integer - question type
        :param caculateCount: Integer - calculate count
        :param postProcess: Integer - post process
        """
        self.name = name
        self.computerTypeId = computerTypeId
        self.inputJFile = inputJFile
        self.inputHFile = inputHFile
        self.questionType = questionType
        self.caculateCount = caculateCount
        self.postProcess = postProcess

    def to_dict(self):
        """
        Convert the request object to dictionary for API request.
        
        :return: Dictionary representation of the request object
        """
        return {
            "name": self.name,
            "computerTypeId": self.computerTypeId,
            "inputJFile": self.inputJFile,
            "inputHFile": self.inputHFile,
            "questionType": self.questionType,
            "caculateCount": self.caculateCount,
            "postProcess": self.postProcess
        }

    def from_dict(self, data):
        """
        Populate the request object from dictionary.
        
        :param data: Dictionary containing the request data
        """
        self.name = data.get("name")
        self.computerTypeId = data.get("computerTypeId")
        self.inputJFile = data.get("inputJFile")
        self.inputHFile = data.get("inputHFile")
        self.questionType = data.get("questionType")
        self.caculateCount = data.get("caculateCount")
        self.postProcess = data.get("postProcess")