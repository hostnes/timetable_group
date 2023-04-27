from aiogram.dispatcher.filters.state import State, StatesGroup


class InstallGroupState(StatesGroup):
    get_group = State()