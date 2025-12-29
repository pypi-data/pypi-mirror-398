class MessageTextNotEnteredError(Exception):
    def __init__(self, message="Message text was not provided"):
        super().__init__(message)


class UnknownQuestionTypeError(Exception):
    def __init__(self, message="Unknown question type."):
        super().__init__(message)


class NoQuestionsEnteredError(Exception):
    def __init__(self, message="No questions were added."):
        super().__init__(message)

class QuestionNotFountError(Exception):
    def __init__(self, question_type:str):
        super().__init__(f"Тип вопроса {question_type} не поддерживается")