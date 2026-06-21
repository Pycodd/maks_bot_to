from imports import (StatesGroup, State)


class WaitingStates(StatesGroup):
    """Группа состояний ожидания"""
    waiting_for_message = State()