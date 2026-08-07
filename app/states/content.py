from aiogram.fsm.state import State, StatesGroup


class ContentStates(StatesGroup):
    destination = State()
    audience = State()
    post_format = State()
    tone = State()
    goal = State()
    topic = State()
    confirm_publish = State()

