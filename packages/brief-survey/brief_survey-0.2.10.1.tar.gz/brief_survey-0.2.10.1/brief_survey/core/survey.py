

from aiogram.enums import ContentType
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from humanfriendly.terminal import message
from pydantic import  ValidationError
from aiogram import types, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram_dialog import Dialog, DialogManager, Window, StartMode, setup_dialogs
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.media import StaticMedia
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from pydantic import BaseModel, create_model, Field
from typing import Optional, Callable, Set, Generic, TypeVar, Type, Dict, Tuple, Any, List, Union, Awaitable

from .builders.questions import QuestionBuilder
from .exceptions.questions import NoQuestionsEnteredError, MessageTextNotEnteredError, QuestionNotFountError
from .exceptions.validators import ValidatorNotFountError, EmptyValidatorNameError
from .models.buttons import InfoButtons
from .models.messages import InfoMessages
from .models.question import Question, QuestionType


from .utils.next_question_switcher_decorator import auto_switch_next_question
from ..utils import find_validator_by_name

ResultModelType = TypeVar("ResultModelType", bound=BaseModel)

class BriefSurvey(Generic[ResultModelType]):
    """
        Универсальный динамический опросник для Telegram-ботов на базе aiogram_dialog.

        Позволяет быстро создавать диалоговые опросы с любым числом вопросов и разными типами ответов.
        Вопросы можно добавлять как при инициализации, так и динамически через метод `add_question`.

        Атрибуты:
            questions (List[Question]): Список вопросов опроса.
            save_handler (Callable): Асинхронная функция для сохранения результата опроса.
            result_model (BaseModel): Pydantic-модель для итоговых данных.
            command_start (str): Команда для запуска опроса.
            info_messages (InfoMessages): Сообщения для пользователя (ошибки, подсказки).
            buttons (InfoButtons): Тексты кнопок для управления опросом.
            states_prefix (str): Префикс для состояний FSM.

        Примеры:

        from brief_survey import BriefSurvey
        from pydantic import BaseModel
        from typing import Optional


        class SurveyResult(BaseModel):
            name: Optional[str]
            gender: Optional[str]

        async def save_handler(user_id: int, result:SurveyResult | any):
            #динамическое обращение к полям результата опроса по имени вопроса если не указана модель.
            name = result.mame
            age = result.age
            gender = result.gender
            return
        survey = BriefSurvey(
            save_handler=save_handler,
            result_model=SurveyResult, # Опиционально
            start_command='start_brief' # Можно настраивать команду начала опроса
        )

        """

    def __init__(
            self,
            *,
            save_handler: Callable[[int, Any], Any],
            result_model: Optional[Type[ResultModelType]] = None,
            questions: Optional[List[Question]] = None,
            states_prefix: str = "SurveyStates",
            start_command: str = "start_survey",
            final_reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup = None,
            pre_brief_check: Optional[Callable|Awaitable] = None,
    ):
        """
               Инициализация опросника.

               Example:
               from brief_survey import BriefSurvey
               from pydantic import BaseModel
               from typing import Optional


               class SurveyResult(BaseModel):
                   name: Optional[str]
                    gender: Optional[str]


               #динамическое обращение к полям результата опроса по имени вопроса если не указана модель
               async def save_handler(user_id: int, result:SurveyResult | any):
                    name = result.mame
                    age = result.age
                    gender = result.gender
                    return


               survey = BriefSurvey(
                    save_handler=save_handler,
                    result_model=SurveyResult, #опционально
                    start_command='start_brief' #Можно настраивать команду начала опроса
                )

               Args:
                   save_handler: Асинхронная функция для сохранения результата (user_id, result).
                   result_model: Pydantic-модель результата (опционально, может быть создана автоматически).
                   questions: Список вопросов (можно добавить позже через add_question).
                   states_prefix: Префикс для состояний FSM.
                   start_command: Команда для запуска опроса в Telegram.
               """
        self._questions = questions
        self.save_handler = save_handler
        self.result_model = result_model
        self.command_start = start_command
        self.info_messages: InfoMessages = InfoMessages()
        self.buttons: InfoButtons = InfoButtons()
        self.states_prefix = states_prefix
        self.final_reply_markup = final_reply_markup
        self._dialog = None
        self.state: FSMContext = None
        self.pre_brief_check = pre_brief_check

    @staticmethod
    def _create_states_group(class_name: str, state_names: List[str]):
        attrs = {name: State() for name in state_names}
        group = type(class_name, (StatesGroup,), attrs)
        mapping = {name: getattr(group, name) for name in state_names}
        return group, mapping

    @property
    def questions(self):
        return self._questions

    @property
    def dialog(self) -> Dialog:
        return self._dialog

    @auto_switch_next_question
    async def _process_text_input(self, message: types.Message,dialog: Dialog, manager: DialogManager):
        text = message.text.strip()
        state_name = manager.current_context().state.state.split(":")[1]
        question = self._get_question(state_name)
        if not question:
            await message.answer(self.info_messages.question_not_found)
            return

        if question.validator and not question.validator(text):
            if question.validator_error_message:
                error_text = question.validator_error_message
            else:
                error_text = self.info_messages.invalid_input
            await message.answer(error_text)
            return True

        if question.forced_exit_validator and not question.forced_exit_validator(text):
            await self.forced_exit_on_validation_error_handler(message, manager)
            return True

        manager.current_context().dialog_data[question.name] = text

    @auto_switch_next_question
    async def _process_text_input_with_confirmation(self, message: types.Message, dialog: Dialog, manager: DialogManager):
        text = message.text.strip()
        state_name = manager.current_context().state.state.split(":")[1]

        question = self._get_question(state_name)
        if not question:
            await message.answer(self.info_messages.question_not_found)
            return
        ctx_data = manager.current_context().dialog_data

        ctx_data[f"with_confirm_{state_name}"] = text


        if question.validator and not question.validator(text):
            if not question.validator_error_message:
                error_text = self.info_messages.invalid_input
            else:
                error_text = question.validator_error_message
            await message.answer(error_text)
            return True

        manager.current_context().dialog_data[question.name] = text
        text = f"Подтвердите введенные данные или отправьте данные заново.\n{question.confirm_field_name} {text}"
        try:
            # await message.delete()
            await message.answer(text)

        except Exception as ex:
            print(ex)

    @auto_switch_next_question
    async def _process_choice_selected(self, c: types.CallbackQuery, widget: Button, manager: DialogManager):
        # selected = widget.widget_id
        selected = widget.text.text  # Получаем текст кнопки, а не id (callback_data)
        state_name = manager.current_context().state.state.split(":")[1]

        question = self._get_question(state_name)
        if not question:
            await c.answer(self.info_messages.question_not_found)
            return True

        manager.current_context().dialog_data[question.name] = selected
        await c.answer()

    #Множественный выбор
    @auto_switch_next_question
    async def _process_multi_choice_selected(self, c: types.CallbackQuery, widget: Button, manager: DialogManager):
        selected_text = widget.text.text
        state_name = manager.current_context().state.state.split(":")[1]
        question = self._get_question(state_name)
        if not question:
            await c.answer(self.info_messages.question_not_found)
            return True
        ctx_data = manager.current_context().dialog_data
        multi_selected = ctx_data.get(f"multi_selected_{state_name}", set())


        if selected_text not in multi_selected and  len(multi_selected) >= question.multi_choice_len:
            return await c.answer(self.info_messages.multi_select_length_limitation.format(length=question.multi_choice_len or '100'))
        if not isinstance(multi_selected, set):
            multi_selected = set(multi_selected)

        if selected_text in multi_selected:
            multi_selected.remove(selected_text)
        else:
            multi_selected.add(selected_text)
        ctx_data[f"multi_selected_{state_name}"] = multi_selected
        #todo:Добавить возможность использовать ключи для модели

        # if question.use_key_for_model:
        #     ctx_data[question.name] = ", ".join(multi_selected)
        # else:
        ctx_data[question.name] = ", ".join(multi_selected)
        try:
            await manager.update({
                "question_text": question.text,
                "selected_text": "\n-".join(multi_selected) if multi_selected else "",
            })
            await c.answer(f"Выбрано: {', '.join(multi_selected) if multi_selected else 'ничего'}")
        except:
            pass

    async def _multi_choice_getter(self, dialog_manager: DialogManager, **kwargs):
        ctx = dialog_manager.current_context()
        state_name = ctx.state.state.split(":")[1]
        question = self._get_question(state_name)

        ctx_data = ctx.dialog_data
        multi_selected = ctx_data.get(f"multi_selected_{state_name}", set())
        if not isinstance(multi_selected, set):
            multi_selected = set(multi_selected)
        #todo: language

        return {
            "question_text": question.text if question else "",
            "selected_text": "\nВыбрано:\n-"+"\n-".join(multi_selected) if multi_selected else "",
        }

    def create_multi_select_window(self,question , **kwargs):
        elements = []
        getter = self._multi_choice_getter
        elements.append(Format('{question_text}{selected_text}\n\nВы можете отменить выбор нажав на тот же пункт меню.'))
        if isinstance(question.choices, dict):
            buttons = [
                Button(text=Const(key), id=str(value), on_click=self._process_multi_choice_selected)
                for key, value in question.choices.items()  # type: ignore
            ]
        elif isinstance(question.choices, list):
            buttons = [
                Button(text=Const(label), id=str(i), on_click=self._process_multi_choice_selected)
                for i, (_, label) in enumerate(question.choices)  # type: ignore
            ]
        else:
            buttons = []
        confirm_btn = Button(
            Const(self.buttons.multi_select_confirm),
            id="confirm",
            on_click=self._confirm_multi_choice)
        elements.extend(buttons)
        elements.append(confirm_btn)
        return elements, getter

    @auto_switch_next_question
    async def _confirm_multi_choice(self, c: types.CallbackQuery, widget: Button, manager: DialogManager):
        ctx_data = manager.current_context().dialog_data

        state_name = manager.current_context().state.state.split(":")[1]
        multi_selected = ctx_data.get(f"multi_selected_{state_name}", set())
        question = self._get_question(state_name)

        ctx_data[question.name] = ", ".join(multi_selected)
        await c.answer()

    @auto_switch_next_question
    async def _process_media_input(self, message: types.Message, dialog: Dialog, manager: DialogManager):
        state_name = manager.current_context().state.state.split(":")[1]
        question = self._get_question(state_name)
        if not question:
            await message.answer(self.info_messages.question_not_found)
            return True

        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.video:
            file_id = message.video.file_id
        else:
            await message.answer(self.info_messages.invalid_input)
            return True

        ctx_data = manager.current_context().dialog_data
        media_list = ctx_data.get(question.name, None)
        # if not isinstance(media_list, list):
        #     media_list = [media_list]
        # media_list.append(file_id)

        ctx_data[question.name] = file_id

    @auto_switch_next_question
    async def _process_media_list_input(self, message: types.Message, dialog: Dialog, manager: DialogManager):
        state_name = manager.current_context().state.state.split(":")[1]
        question = self._get_question(state_name)
        if not question:
            await message.answer(self.info_messages.question_not_found)
            return True

        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.video:
            file_id = message.video.file_id
        else:
            await message.answer(self.info_messages.invalid_input)
            return True

        ctx_data = manager.current_context().dialog_data
        media_list = ctx_data.get(question.name, None)
        # if not isinstance(media_list, list):
        #     media_list = [media_list]
        media_list.append(file_id)
        ctx_data[question.name] = media_list
        if question.next_question:
            await manager.switch_to(self.state_map[question.next_question])
        else:
            await manager.next()
        return

    @auto_switch_next_question
    async def _confirm_text_with_confirmation(self, c: types.CallbackQuery, button: Button, manager: DialogManager,*args,**kwargs):
        ctx_data = manager.current_context().dialog_data

        state_name = manager.current_context().state.state.split(":")[1]
        text = ctx_data.get(f"with_confirm_{state_name}", "")
        if not text:
            await c.answer(self.info_messages.no_confirmed_data)
            return
        question = self._get_question(state_name)
        if question.forced_exit_validator and not question.forced_exit_validator(text):
            await self.forced_exit_on_validation_error_handler(c.message, manager)
            return True
        ctx_data[question.name] = text
        await c.answer()

    async def forced_exit_on_validation_error_handler(self, message: types.Message, manager: DialogManager):
        await message.answer(self.info_messages.forced_exit_message)
        await manager.done()

    def _get_question(self, name: str) -> Optional[Question]:

        for q in self.questions:
            if q.name == name:
                return q
        return None

    def _make_window_for_question(self, question: Question) -> Window:
        state = self.state_map[question.name]
        qtext = question.text

        # Базовые элементы окна
        elements = []

        if question.media:
            elements.append(StaticMedia(path=question.media))
        getter =None
        # Обработка по типу вопроса
        if question.type in ["text", "number"]:
            elements.append(Const(qtext))
            elements.append(MessageInput(self._process_text_input))
        elif question.type =="with_confirm":
            elements.append(MessageInput(self._process_text_input_with_confirmation))
            elements.append(Const(qtext))
            confirm_btn = Button(Const(f"Подтвердить {question.confirm_field_name.replace(':','')}"
                if question.confirm_field_name  else self.buttons.confirm_entered_text), id="confirm_text",
                                 on_click=self._confirm_text_with_confirmation)
            elements.append(confirm_btn)
        elif question.type == "choice":
            elements.append(Const(qtext))
            if isinstance(question.choices,dict):
                buttons = [
                Button(text=Const(label), id=key, on_click=self._process_choice_selected)
                for key, label in question.choices  # type: ignore
                ]
            elif isinstance(question.choices,list):
                buttons = [
                Button(text=Const(label), id=str(i), on_click=self._process_choice_selected)
                for i, (_, label) in enumerate(question.choices)  # type: ignore
                ]
            else:
                buttons = []
            elements.extend(buttons)
        elif question.type == "multi_choice":
            elements, getter = self.create_multi_select_window(question)

        elif question.type in ["photo", "video", "media"]:
            elements.append(Const(qtext))
            if question.type == "photo":
                allowed_types = [ContentType.PHOTO]
            elif question.type == "video":
                allowed_types = [ContentType.VIDEO]
            else:
                allowed_types = [ContentType.PHOTO, ContentType.VIDEO]
            elements.append(MessageInput(self._process_media_input, content_types=allowed_types))
        else:
            raise QuestionNotFountError(question.type)

        return Window(*elements, state=state,getter=getter)

    async def _on_finish(self, c: types.CallbackQuery, button, manager: DialogManager):
        data = manager.current_context().dialog_data
        user_id = c.from_user.id
        try:
            result_obj = self.result_model.model_validate(data)
        except ValidationError as e:
            await c.message.answer(f"Некорректные данные:\n" + "\n".join(
                [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            ))
            return True

        mes = await c.message.answer(self.info_messages.pre_save_message)
        markup = None
        if self.final_reply_markup:
            markup = self.final_reply_markup
        try:
            await self.save_handler(user_id, result_obj)
        except Exception as e:
            print("Save handler error:", e)
            await c.message.answer(self.info_messages.save_fail, reply_markup=markup)
        else:
            await c.message.answer(self.info_messages.save_success, reply_markup=markup)
        finally:
            await mes.delete()
            await c.message.delete()
            await manager.done()
            await self.state.clear()

    async def pre_brief_check(self, message: types.Message):
        if self.pre_brief_check:
            if isinstance(self.pre_brief_check, Awaitable):
                if await self.pre_brief_check(message):
                    await message.answer(self.info_messages.pre_brief_check_fail)
                    return
            if isinstance(self.pre_brief_check, Callable):
                if await self.pre_brief_check(message):
                    await message.answer(self.info_messages.pre_brief_check_fail)
                    return
    async def start(self, message: types.Message, dialog_manager: DialogManager, state: FSMContext):

        first_state_name = self.questions[0].name if self.questions else None
        if self.info_messages.start_message:
            await message.answer(self.info_messages.start_message)
        if first_state_name:
            self.state = state
            await state.set_state(self.state_map[first_state_name])
            await dialog_manager.start(self.state_map[first_state_name], mode=StartMode.RESET_STACK)
        else:
            await message.answer("Извините, еще нет вопросов для опроса.")

    async def _start_again(self, c: types.CallbackQuery, button, manager: DialogManager):
        first_state_name = self.questions[0].name if self.questions else None
        if first_state_name:
            await self.state.set_state(self.state_map[first_state_name])
            await manager.start(self.state_map[first_state_name], mode=StartMode.RESET_STACK)
        else:
            await c.message.answer("Извините, еще нет вопросов для опроса.")

    async def cmd_start_survey_handler(
            self,
            message: types.Message,
            dialog_manager: DialogManager,
            state: FSMContext,
    ):
        await self.start(message, dialog_manager, state)

    def register_handlers(self, dp: Dispatcher,
                          command_start: str = None,
                          callback_data: str = None,
                          text: str = None,
                          ):
        """
        Регистрирует все необходимые хендлеры для запуска и работы опроса в Telegram-боте.

        Args:
            dp (Dispatcher): Диспетчер aiogram.
            command_start (str, optional): Команда для запуска опроса.
            callback_data (str, optional): Callback data для запуска опроса по кнопке.
            text (str, optional): Текст сообщения для запуска опроса.
        """
        if not self.questions:
            raise NoQuestionsEnteredError
        else:
            self.create_result_model_from_questions()
        if command_start:
            dp.message.register(self.cmd_start_survey_handler, Command(command_start))
        else:
            dp.message.register(self.cmd_start_survey_handler, Command(self.command_start))
        if callback_data:
            dp.callback_query.register(self.cmd_start_survey_handler, F.data == callback_data)
        if text:
            dp.message.register(self.cmd_start_survey_handler, F.text == text)
        self.States, self.state_map = self._create_states_group(
            class_name=self.states_prefix,
            state_names=[q.name for q in self.questions] + ["finish"],
        )

        self.windows = [self._make_window_for_question(q) for q in self.questions]
        self.windows.append(
            Window(
                Const(self.info_messages.finish_text),

                Button(Const(self.buttons.finish_text), id="finish", on_click=self._on_finish),
                Button(Const(self.buttons.start_again), id="start_again", on_click=self._start_again),
                state=self.state_map["finish"],
            )
        )

        self._dialog = Dialog(*self.windows)
        dp.include_router(self.dialog)
        setup_dialogs(dp)

    def add_question(
            self,
            text: str,
            question_type: QuestionType = "text",
            name: str = None,
            choices: Optional[List[str] | Tuple[str] | Set[str] | Dict[str, str]] = None,
            validator: Optional[Callable[[str], bool] | str] = None,
            next_questions: Optional[Dict[str, str]] = None,  # например {"Yes": "q3", "No": "q4"},
            next_question: Optional[str] = None,  # name следующего вопроса, нужно для ветвления запросов
            media_path: Optional[str] = None,
            forced_exit_validator: Optional[Callable[[str], bool]] = None,
            validate_by_question_name: bool = True,
            validator_error_message: Optional[str] = None,
            confirm_field_name: Optional[str] = None,
            multy_choice_len: Optional[int] = 100,
            *args,
            **kwargs
    ) -> Question:
        """
               Добавляет новый вопрос в опросник.

               Args:
                   text (str): Текст вопроса (обязателен).
                   question_type (str): Тип вопроса: "text", "number", "choice", "multi_choice", "photo", "video", "media".
                   name (str, optional): Уникальное имя вопроса (если не указано — генерируется автоматически).
                   choices (list, optional): Список вариантов для "choice" и "multi_choice". Dict for multi_choice only
                   validator (Callable, optional): Функция-валидатор для ответа.
                   next_questions (dict, optional): Словарь переходов к следующим вопросам по ответу.
                   next_question (str, optional): Имя следующего вопроса (для линейного перехода).
                   media_path (str, optional): Путь к медиафайлу (картинка, видео).
                   *args: Дополнительные позиционные аргументы.
                   **kwargs: Дополнительные именованные аргументы.

               Raises:
                   MessageTextNotEnteredError: Если текст вопроса пустой.

               Пример:
                   survey.add_question(
                       text="Ваш возраст?",
                       question_type="number",
                       name="age",
                       validator=lambda x: x.isdigit() and 0 < int(x) < 120,
                       choices=["Да", "Нет"],

                   )
                   :param text:
                   :param question_type:
                   :param name:
                   :param choices:
                   :param validator:
                   :param next_questions:
                   :param next_question:
                   :param media_path:
                   :param validator_error_message:
                   :param validate_by_question_name:
                   :param forced_exit_validator:
                   :param multi_choice_len:
               """

        if not text:
            raise MessageTextNotEnteredError("Текст вопроса не может быть пустым.")
        if choices:
            if isinstance(choices, dict):
                choices = [(key, value) for key, value in choices.items()]
            else:
                choices = [(str(i[0]), i[1]) for i in enumerate(choices)]
        if choices and question_type == "text":
            question_type = 'choice'
        if not name:
            name = f"q{len(self.questions) + 1}"

        # TODO: вынести валидатор в отдельный метод
        # TODO: Добавить к валидатору готовый набор функций.
        # Например:имени, выбора дней недели и тд...
        if type(validator) == str:
            find_validator = find_validator_by_name(validator)
            if not find_validator:
                raise ValidatorNotFountError(validator)
            validator = find_validator
        if not validator and validate_by_question_name:
            find_validator = find_validator_by_name(name)
            validator = find_validator

        question_model = QuestionBuilder.create(
            text=text,
            question_type=question_type,
            name=name,
            choices=choices,
            validator=validator,
            next_questions=next_questions,
            next_question=next_question,
            media=media_path,
            forced_exit_validator=forced_exit_validator,
            validator_error_message=validator_error_message,
            confirm_field_name=confirm_field_name,
            multi_choice_len=multy_choice_len,
            *args,
            **kwargs
        )
        if not self.questions:
            self._questions = []
        self._questions.append(question_model)
        return question_model

    @staticmethod
    def get_field_type_and_default(question_type: str) -> Tuple[Any, Any]:

        if question_type in ("text", "choice", "multi_choice"):
            return (str, Field(default=None))
        elif question_type == "number":
            return (float, Field(default=None))
        elif question_type in ("photo", "video"):
            return (Optional[str], Field(default=None))
        elif question_type in ("media"):
            return (Optional[List[str]], Field(default_factory=list))
        else:
            return (str, Field(default=None))

    def create_result_model_from_questions(self) -> BaseModel:
        """
                Автоматически создает Pydantic-модель результата на основе списка вопросов.

                Returns:
                    BaseModel: Класс модели результата для сериализации итоговых данных пользователя.
                """
        fields: Dict[str, Tuple[Any, Any]] = {}

        for q in self.questions:
            field_type, default = self.get_field_type_and_default(q.type)
            fields[q.name] = (field_type, default)
        if not self.result_model:
            self.result_model = create_model('DynamicResultModel', **fields)
            return self.result_model
        else:
            model = create_model('DynamicResultModel', **fields)
            return model


