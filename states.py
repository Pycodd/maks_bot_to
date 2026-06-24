from imports import (StatesGroup, State)


class WaitingStates(StatesGroup):
    """Группа состояний ожидания"""
    waiting_for_message = State()


class RegistrationStates(StatesGroup):
    """Группа состояний для регистрации"""
    waiting_for_agreement = State()      # ожидание принятия соглашения
    waiting_for_district = State()       # ожидание выбора района
    waiting_for_address = State()        # ожидание ввода адреса
    waiting_for_entrance = State()       # ожидание ввода подъезда
    waiting_for_floor = State()          # ожидание ввода этажа
    waiting_for_apartment = State()      # ожидание ввода квартиры
    waiting_for_phone = State()          # ожидание ввода телефона
    waiting_for_confirmation = State()   # ожидание подтверждения