from imports import (
    InlineKeyboardBuilder,
    LinkButton,
    CallbackButton,
    MessageButton,
    RequestContactButton,
    RequestGeoLocationButton
)


class Keyboards:
    """
    Универсальный класс для всех клавиатур бота.
    """

    @staticmethod
    def main_menu():
        """
        Главное меню бота.
        Возвращает: (клавиатура, текст)
        """
        builder = InlineKeyboardBuilder()

        builder.row(LinkButton(text="📚 Документация", url="https://dev.max.ru/docs"))
        builder.row(
            CallbackButton(text="⚙️ Настройки", payload="settings"),
            CallbackButton(text="ℹ️ О боте", payload="about")
        )
        builder.row(CallbackButton(text="✉️ Написать сообщение", payload="write_message"))
        builder.row(RequestContactButton(text="📞 Отправить контакт"))
        builder.row(RequestGeoLocationButton(text="Геолокация"))

        return builder.as_markup(), "📋 Главное меню:"
