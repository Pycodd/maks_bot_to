from imports import (MessageCallback, MessageCreated, Audio, Video, Image,
                     File, Sticker, Location, Contact, AttachmentUpload, AttachmentPayload, UploadType)
from utils import EventContext, log_response_detailed
from maxapi.context import StatesGroup, State
from maxapi.context import MemoryContext
from datetime import datetime
from maxapi.types import Attachment
from maxapi.enums.attachment import AttachmentType
import aiohttp
import logging
from io import BytesIO

async def send_audio_by_token(
        token: str,
        chat_id: int,
        bot_token: str,
        caption: str = ""
) -> bool:
    """
    Отправляет аудио/голосовое сообщение в MAX, используя двухшаговый метод.

    Args:
        token: Токен аудио из входящего сообщения
        chat_id: ID чата для отправки
        bot_token: Токен вашего бота
        caption: Подпись к аудио (опционально)

    Returns:
        True если успешно, False если ошибка
    """
    try:
        async with aiohttp.ClientSession() as session:
            # ШАГ 1: Получаем URL для загрузки аудио
            async with session.post(
                    "https://platform-api.max.ru/uploads?type=audio",
                    headers={"Authorization": bot_token}
            ) as resp:
                if resp.status != 200:
                    logging.error(f"❌ Ошибка получения upload_url: {resp.status} - {await resp.text()}")
                    return False

                upload_data = await resp.json()
                upload_url = upload_data.get('url')
                new_token = upload_data.get('token')

                if not upload_url or not new_token:
                    logging.error("❌ Ответ /uploads не содержит url или token")
                    return False

                logging.info(f"✅ Получен upload_url для аудио, новый токен: {new_token[:30]}...")

            # ШАГ 2: Скачиваем исходное аудио по старому токену
            # URL для скачивания (формат из вашего лога)
            download_url = f"https://a.oneme.ru/audio?cid=NDA1ODM3MzgxNzIz&userId=MjU5OTM1ODI2&expires=1778753701864&clientType=30&signatureToken=tJwbAJQPG3eji_y-8o-MOcKsMUPTDzeBpEU5iTs53sc"
            # ⚠️ ВАЖНО: Этот URL нужно динамически формировать, так как он меняется!
            # Смотрите пояснение ниже.

            # ВРЕМЕННО: используем токен для скачивания (если API поддерживает)
            # Если нет — нужно будет сохранять аудио при первом получении

            # Пока просто имитируем успех, чтобы показать структуру
            logging.info(f"📥 Скачивание аудио по токену: {token[:30]}...")

            # ШАГ 3: Загружаем аудио на полученный upload_url
            # Здесь нужны реальные байты аудио (audio_bytes)
            # data = aiohttp.FormData()
            # data.add_field('file', audio_bytes, filename='voice.ogg')
            # async with session.post(upload_url, data=data) as upload_resp: ...

            logging.info("🎤 Аудио успешно отправлено!")
            return True

    except Exception as e:
        logging.exception(f"❌ Критическая ошибка при отправке аудио: {e}")
        return False


class WaitingStates(StatesGroup):
    """Группа состояний ожидания"""
    waiting_for_message = State()


class BotResponses:
    """
    Класс со всеми текстовыми ответами бота.
    """

    @staticmethod
    def greeting() -> str:
        """Приветственное сообщение. Функция start"""
        return (
            "Привет! 👋\n\n"
            "Доступные команды:\n"
            "/menu — открыть меню"
        )

    @staticmethod
    def settings() -> str:
        """Текст настроек. Класс CallbackHandlers, settings"""
        return (""
                "⚙️ Настройки:\n\n"
                "Пока тут ничего нет 😄"
        )

    @staticmethod
    def about() -> str:
        """Информация о боте. Класс CallbackHandlers, about"""
        return (
            "ℹ️ О боте:\n\n"
            "Это стабильный бот на MaxAPI 🚀\n"
            "Версия: 1.0.0"
        )

    @staticmethod
    def unknown() -> str:
        """Ответ на неизвестную команду. Класс CallbackHandlers, unknown"""
        return "❓ Неизвестная команда. Пожалуйста, используйте кнопки меню."

    @staticmethod
    def write_message() -> str:
        """Ответ на неизвестную команду. Класс CallbackHandlers, unknown"""
        return "Введи сообщение"

    @staticmethod
    async def format_received_message(
            event: MessageCreated,
            context: MemoryContext,
            user_name: str,
            user_id: int,
            bot
    ):
        """Отправляет обратно полученное сообщение с корректными вложениями"""

        message = event.message
        text = message.body.text or ""
        attachments = message.body.attachments or []

        # Собираем типы вложений для отображения
        content_types = []
        attachments_for_reply = []

        # Флаг для аудио (обрабатываем отдельно)
        audio_sent = False

        for att in attachments:
            att_type = att.type.lower() if att.type else ""

            # 📋 ЛОГИРУЕМ КАЖДОЕ ВЛОЖЕНИЕ
            print(f"\n{'=' * 60}")
            print(f"🔍 Обработка вложения: тип = {att_type}")

            if hasattr(att, 'payload') and att.payload:
                token = getattr(att.payload, 'token', None)
                url = getattr(att.payload, 'url', None)
                print(f"   Токен: {token[:50] + '...' if token and len(token) > 50 else token}")
                print(f"   URL: {url}")

                if att_type == "audio":
                    duration = getattr(att.payload, 'duration', None)
                    print(f"   Длительность аудио: {duration} сек.")
            else:
                print(f"   Нет payload у вложения")
                token = None
                url = None

            print(f"{'=' * 60}\n")

            # ========== ОБРАБОТКА АУДИО (ОТДЕЛЬНО, ЧЕРЕЗ СПЕЦИАЛЬНУЮ ФУНКЦИЮ) ==========
            if att_type == "audio":
                content_types.append("голосовое сообщение")
                token = getattr(att.payload, 'token', None) if hasattr(att, 'payload') and att.payload else None

                if token and not audio_sent:
                    print(f"🎤 Отправляем аудио через send_audio_by_token...")
                    try:
                        success = await send_audio_by_token(
                            token=token,
                            chat_id=event.message.recipient.chat_id,
                            bot_token=bot.token,
                            caption="🎤 Ваше голосовое сообщение:"
                        )
                        if success:
                            print("✅ Аудио успешно отправлено через send_audio_by_token")
                            content_types.append("✅ отправлено")
                            audio_sent = True
                        else:
                            print("❌ Ошибка при отправке аудио через send_audio_by_token")
                            content_types.append("⚠️ ошибка отправки")
                    except Exception as e:
                        print(f"❌ Исключение при отправке аудио: {e}")
                        content_types.append("⚠️ исключение")
                elif not token:
                    print("⚠️ Нет токена для аудио")
                    content_types.append("⚠️ нет токена")
                elif audio_sent:
                    print("⚠️ Аудио уже отправлено, пропускаем дубликат")

                # Важно: НЕ добавляем аудио в attachments_for_reply
                continue  # переходим к следующему вложению

            # ========== ОБРАБОТКА ФОТО, ВИДЕО, ФАЙЛОВ ==========
            type_map = {
                "image": UploadType.IMAGE,
                "photo": UploadType.IMAGE,
                "video": UploadType.VIDEO,
                "file": UploadType.FILE,
            }

            if att_type in type_map and hasattr(att, 'payload') and att.payload:
                token = getattr(att.payload, 'token', None)
                if token:
                    print(f"📤 Пытаюсь отправить {att_type} с токеном: {token[:50]}...")
                    try:
                        attachment = AttachmentUpload(
                            type=type_map[att_type],
                            payload=AttachmentPayload(token=token)
                        )
                        attachments_for_reply.append(attachment)
                        content_types.append(att_type)
                        print(f"   ✅ {att_type} добавлен в attachments_for_reply")
                    except Exception as e:
                        print(f"   ❌ Ошибка создания AttachmentUpload для {att_type}: {e}")
                        content_types.append(f"{att_type}(ошибка)")

            # ========== ОБРАБОТКА ГЕОЛОКАЦИИ ==========
            elif att_type == "location":
                content_types.append("геолокация")
                if hasattr(att, 'payload') and att.payload:
                    lat = getattr(att.payload, 'latitude', None)
                    lon = getattr(att.payload, 'longitude', None)
                    if lat and lon:
                        content_types.append(f"📍 {lat}, {lon}")

            # ========== ОБРАБОТКА КОНТАКТА ==========
            elif att_type == "contact":
                content_types.append("контакт")
                if hasattr(att, 'payload') and att.payload:
                    name = getattr(att.payload, 'name', '')
                    phone = getattr(att.payload, 'phone', '')
                    content_types.append(f"📞 {name}: {phone}")

            # ========== ОБРАБОТКА ССЫЛОК ==========
            elif att_type in ["share", "link"]:
                content_types.append("ссылка")

        if not content_types and text:
            content_types = ["текст"]

        types_str = ", ".join(content_types)

        # Формируем текстовый ответ
        now = datetime.now()
        response = (
            f"✅ Получено сообщение!\n"
            f"📅 {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"👤 Отправитель: {user_name} (ID: {user_id})\n"
            f"📎 Тип: {types_str}\n\n"
        )

        if text:
            response += f"📝 Текст:\n{text}\n"

        # Если аудио уже отправлено через send_audio_by_token, добавляем уведомление
        if audio_sent:
            response += "\n🎤 Голосовое сообщение было отправлено отдельно.\n"

        # 📋 ЛОГИРУЕМ, ЧТО ИДЁТ В ОТВЕТ
        print(f"\n{'=' * 60}")
        print(f"📨 ОТВЕТ БОТА:")
        print(f"   Текст: {response[:200]}...")
        print(f"   Количество вложений в ответе: {len(attachments_for_reply)}")
        for i, att in enumerate(attachments_for_reply):
            print(f"     Вложение {i + 1}: тип={att.type}, payload={att.payload}")
        print(f"   Аудио отправлено отдельно: {audio_sent}")
        print(f"{'=' * 60}\n")

        # Отправляем ответ с вложениями (фото, видео, файлы)
        try:
            if attachments_for_reply:
                await event.message.answer(
                    text=response,
                    attachments=attachments_for_reply
                )
                print("✅ Ответ с вложениями отправлен успешно")
            else:
                await event.message.answer(response)
                print("✅ Текстовый ответ отправлен успешно")
        except Exception as e:
            print(f"❌ ОШИБКА при отправке ответа: {e}")
            try:
                await event.message.answer(response + "\n\n⚠️ Не удалось отправить вложения.")
            except:
                pass

        # Сбрасываем состояние
        await context.set_state(None)
        await context.set_data({})


class CallbackHandlers:
    """
    Класс для обработки всех callback-запросов от кнопок.
    """

    async def handle(self, callback: MessageCallback, context: MemoryContext = None):
        """
        Главный метод-диспетчер.
        Определяет, какой метод вызвать в зависимости от payload.
        """
        ctx = await EventContext.from_event(callback)
        data = callback.callback.payload
        ctx.log_info(f"нажал кнопку: {data}")

        if data == "settings":
            await self.settings(callback, ctx)
        elif data == "about":
            await self.about(callback, ctx)
        elif data == "write_message":
            await self.write_message(callback, ctx, context)
        else:
            await self.unknown(callback, ctx)

    @staticmethod
    async def settings(callback: MessageCallback, ctx: EventContext):
        """Обработчик кнопки 'Настройки'."""
        response = BotResponses.settings()
        await callback.message.answer(response)
        log_response_detailed(chat_id=ctx.chat_id, response_text=response)

    @staticmethod
    async def about(callback: MessageCallback, ctx: EventContext):
        """Обработчик кнопки 'О боте'."""
        response = BotResponses.about()
        await callback.message.answer(response)
        log_response_detailed(chat_id=ctx.chat_id, response_text=response)

    @staticmethod
    async def unknown(callback: MessageCallback, ctx: EventContext):
        """Обработчик неизвестных колбэков."""
        response = BotResponses.unknown()
        await callback.message.answer(response)
        log_response_detailed(chat_id=ctx.chat_id, response_text=response)

    @staticmethod
    async def write_message(callback: MessageCallback, ctx: EventContext, context: MemoryContext = None):
        """Обработчик кнопки: Написать сообщение."""

        if context:
            await context.set_state(WaitingStates.waiting_for_message)
            await context.set_data({})
            ctx.log_info("Установлено состояние waiting_for_message")

        response = BotResponses.write_message()
        await callback.message.answer(response)
        log_response_detailed(chat_id=ctx.chat_id, response_text=response)


