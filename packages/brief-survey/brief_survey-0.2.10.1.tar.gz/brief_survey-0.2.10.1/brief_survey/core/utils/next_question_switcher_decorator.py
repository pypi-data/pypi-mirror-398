from functools import wraps
from aiogram_dialog.manager.manager import ManagerImpl
from aiogram_dialog.widgets.kbd import Button

def auto_switch_next_question(func):
    """
    Декоратор для методов класса, который после выполнения
    переключит состояние в диалоге, используя self из метода.
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)
        if result:
            return
        manager = kwargs.get("manager", None)
        widget = kwargs.get("widget", None)
        for arg in args:
            if isinstance(arg, ManagerImpl):
                manager = arg
            if isinstance(arg, Button):
                widget = arg
        if not manager:
            return result

        state_name = manager.current_context().state.state.split(":")[1]
        question = self._get_question(state_name)

        if question:
            next_state_name = None
            selected = manager.current_context().dialog_data.get(question.name, None)
            if question.next_questions and selected in question.next_questions:
                next_state_name = question.next_questions[selected]
            elif question.next_question:
                next_state_name = question.next_question

            if question.type == 'with_confirm' and widget and widget.widget_id == "confirm_text":
                if not selected:
                    return result
                if next_state_name:
                    await manager.switch_to(self.state_map[next_state_name])
                else:
                    await manager.next()
            elif question.type == 'with_confirm' and selected:
                return result
            elif question.type == 'multi_choice' and widget.widget_id == "confirm":
                if next_state_name:
                    await manager.switch_to(self.state_map[next_state_name])
                else:await manager.next()
            elif question.type == 'multi_choice' and selected:
                return result
            elif next_state_name:
                await manager.switch_to(self.state_map[next_state_name])
            else:
                await manager.next()

        return result

    return wrapper

