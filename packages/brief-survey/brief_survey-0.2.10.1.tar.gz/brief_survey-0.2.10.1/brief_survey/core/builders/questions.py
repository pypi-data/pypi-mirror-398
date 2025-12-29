from typing import Optional, List, Callable, Dict

from brief_survey.core.models.question import QuestionBase
from brief_survey.core.exceptions.questions import UnknownQuestionTypeError
from brief_survey.core.models.question import QUESTION_TYPE_MAP


class QuestionBuilder:
    def __init__(self, question: QuestionBase):
        self.question = question

    @staticmethod
    def create(question_type: str,
               name: str,
               text: str,
               choices: Optional[List[tuple]] = None,
               validator:Callable=None,
               next_questions: Optional[Dict[str, str]] = None,
               next_question: Optional[str] = None,  # name следующего вопроса, нужно для ветвления запросов
               media: Optional[str] = None,
               validator_error_message:Optional[str] = None,
               confirm_field_name:Optional[str]=None,
               multi_choice_len:Optional[int]=None,
               *args,
               **kwargs) -> 'QuestionBase':
        model_cls = QUESTION_TYPE_MAP.get(question_type)
        if not model_cls:
            raise UnknownQuestionTypeError
        return model_cls(name=name,
                         text=text,
                         type=question_type,
                         choices=choices,
                         validator=validator,
                         next_questions=next_questions,
                         next_question=next_question,
                         media=media,
                         validator_error_message=validator_error_message,
                         confirm_field_name=confirm_field_name,
                         multi_choice_len=multi_choice_len,
                         *args,
                         **kwargs
                         )
