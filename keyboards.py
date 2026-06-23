from imports import (InlineKeyboardBuilder, LinkButton, CallbackButton, RequestContactButton, RequestGeoLocationButton)


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

    @staticmethod
    def main_menu_keyboard():
        """
        Только клавиатура главного меню (без текста).
        Возвращает: клавиатура (можно использовать в attachments)
        """
        builder = InlineKeyboardBuilder()

        builder.row(LinkButton(text="📚 Документация", url="https://dev.max.ru/docs"))
        builder.row(
            CallbackButton(text="⚙️ Настройки", payload="settings"),
            CallbackButton(text="ℹ️ О боте", payload="about")
        )
        builder.row(CallbackButton(text="✉️ Написать сообщение", payload="write_message"))
        builder.row(RequestContactButton(text="📞 Отправить контакт"))
        builder.row(RequestGeoLocationButton(text="📍 Геолокация"))

        return builder.as_markup()

    @staticmethod
    def default_keyboard():
        """
        Клавиатура по умолчанию (для ответов на любые сообщения).
        Возвращает: клавиатура (можно использовать в attachments)
        """
        builder = InlineKeyboardBuilder()

        builder.row(
            CallbackButton(text="⚙️ Настройки", payload="settings"),
            CallbackButton(text="ℹ️ О боте", payload="about"))
        builder.row(CallbackButton(text="✉️ Написать сообщение", payload="write_message"))
        builder.row(
            RequestContactButton(text="📞 Отправить контакт"),
            RequestGeoLocationButton(text="📍 Геолокация")
        )

        return builder.as_markup()

    @staticmethod
    def ten_buttons_horizontal():
        """
        Клавиатура из 10 кнопок в один ряд (горизонтально).
        Возвращает: клавиатура
        """
        builder = InlineKeyboardBuilder()

        builder.row(CallbackButton(text="111111111111111111111111111111111", payload="num_1"))
        builder.row(CallbackButton(text="222222222222222222222222222222222", payload="num_2"))
        builder.row(CallbackButton(text="333333333333333333333333333", payload="num_3"))
        builder.row(CallbackButton(text="4444444444444444", payload="num_4"))
        builder.row(CallbackButton(text="55555555555555555555555555", payload="num_5"))
        builder.row(CallbackButton(text="666666666666666666666666", payload="num_6"))
        builder.row(CallbackButton(text="77777777777777777777777777777", payload="num_7"))
        builder.row(CallbackButton(text="8", payload="num_8"))
        builder.row(CallbackButton(text="9", payload="num_9"))
        builder.row(CallbackButton(text="10", payload="num_10"))

        builder.row(
            CallbackButton(text="<<", payload="back_to_menu"),
            CallbackButton(text="---", payload="main_menu"),
            CallbackButton(text=">>", payload="close")
        )

        return builder.as_markup()
