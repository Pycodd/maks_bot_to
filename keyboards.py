from imports import (InlineKeyboardBuilder, LinkButton, CallbackButton, RequestContactButton, RequestGeoLocationButton)


class Keyboards:
    """
    Универсальный класс для всех клавиатур бота.
    """

    @staticmethod
    def main_menu():
        """
        Возвращает: (клавиатура, текст)
        """
        builder = InlineKeyboardBuilder()
        builder.row(CallbackButton(text="✉️ Написать сообщение", payload="write_message"))

        return builder.as_markup(), "📋 Главное меню:"

    @staticmethod
    def create_user_keyboard_district_and_map():
        """
        Создаёт клавиатуру с районами и словарь для сопоставления callback_data и их названий.

        Возвращает:
            tuple: (InlineKeyboardMarkup, dict) — клавиатура и словарь названий районов.
        """
        # Словарь для сопоставления callback_data с названиями районов
        district_names = {
            "Dzerzhinsky": "Дзержинский",
            "Central": "Центральный",
            "Krasnooktyabrsky": "Краснооктябрьский",
            "Voroshilovsky": "Ворошиловский",
            "Soviet": "Советский",
            "Kirov": "Кировский",
            "Tractor": "Тракторный",
            "Spartanovka": "Спартановка",
            "Krasnoarmeysky": "Красноармейский",
        }

        # Создаём клавиатуру
        builder = InlineKeyboardBuilder()

        # Каждая кнопка в отдельном ряду (как в телеграме)
        for callback_data, display_name in district_names.items():
            builder.row(CallbackButton(
                text=display_name,
                payload=f"district_{callback_data}"  # payload: district_Dzerzhinsky
            ))

        # Кнопка "Отменить" (в отдельном ряду)
        builder.row(CallbackButton(
            text="❌ Отменить",
            payload="district_cancel"
        ))

        return builder.as_markup(), district_names

    @staticmethod
    def agreement_keyboard():
        """
        Клавиатура для принятия пользовательского соглашения.
        """
        builder = InlineKeyboardBuilder()

        builder.row(CallbackButton(
            text="✅ Принять и продолжить",
            payload="agreement_accept"
        ))

        builder.row(CallbackButton(
            text="❌ Отказаться",
            payload="agreement_decline"
        ))

        return builder.as_markup()
