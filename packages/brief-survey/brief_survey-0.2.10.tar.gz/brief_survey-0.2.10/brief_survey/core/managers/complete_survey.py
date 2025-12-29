from typing import List

from brief_survey import QuestionBase
from brief_survey.core.db.repositories.base import BaseRepository, T


# class CreditsRepository(BaseRepository[Credits]):
#     def __init__(self):
#         super().__init__(
#             sql_model_class=Credits,
#             async_mode=True,
#             connection_string=async_url,
#         )

class CompleteSurveyManager:
    def __init__(self,
                 repository:BaseRepository[T]=None,
                 db_tablename:str="Survey"
                 ):
        self.repo = None

    async def asave_survey(self,name:str,questions:List[QuestionBase]):
        ...

    def save_survey(self,name:str,questions:List[QuestionBase]):
        ...

    async def aget_survey_by_name(self,name:str):
        ...

    def get_survey_by_name(self,name:str):
        ...

    async def aget_survey_by_id(self,idx:str|int):
        ...

    def get_survey_by_id(self,idx:str|int):
        ...