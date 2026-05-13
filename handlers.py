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
from maxapi.enums.sender_action import SenderAction
from maxapi.types.attachments.audio import Audio
from maxapi.types.attachments.file import File
from maxapi.types.attachments.image import Image
from maxapi.types.attachments.sticker import Sticker
from maxapi.types.attachments.video import Video


async def send_audio_by_token(
        audio_url: str,
        chat_id: int,
        bot_token: str,
        caption: str = ""
) -> bool:
    """
    Отправляет аудио/голосовое сообщение в MAX с подробным логированием.
    """

    print("=" * 70)
    print("🔊🔊🔊 send_audio_by_token ВЫЗВАНА 🔊🔊🔊")
    print(f"   audio_url: {audio_url[:100] if audio_url else 'None'}...")
    print(f"   chat_id: {chat_id}")
    print(f"   caption: {caption}")
    print(f"   bot_token: {bot_token[:20] if bot_token else 'None'}...")
    print("=" * 70)

    try:
        async with aiohttp.ClientSession() as session:
            # ========== ШАГ 1: ПОЛУЧАЕМ UPLOAD_URL ==========
            print("\n📡 ШАГ 1: Запрашиваю upload_url у MAX API...")
            print(f"   URL: https://platform-api.max.ru/uploads?type=audio")
            print(f"   Headers: Authorization: {bot_token[:20]}...")

            async with session.post(
                    "https://platform-api.max.ru/uploads?type=audio",
                    headers={"Authorization": bot_token}
            ) as resp:
                print(f"   Ответ от /uploads: status={resp.status}")

                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"   ❌ ОШИБКА: status {resp.status}")
                    print(f"   Текст ошибки: {error_text}")
                    return False

                upload_data = await resp.json()
                print(f"   ✅ Получены данные: {upload_data}")

                upload_url = upload_data.get('url')
                new_token = upload_data.get('token')

                print(f"   upload_url: {upload_url[:80] if upload_url else 'None'}...")
                print(f"   new_token: {new_token[:40] if new_token else 'None'}...")

                if not upload_url or not new_token:
                    print("   ❌ ОШИБКА: Ответ не содержит url или token")
                    return False

                print("   ✅ upload_url и token получены успешно")

            # ========== ШАГ 2: СКАЧИВАЕМ АУДИО ПО URL ==========
            print(f"\n📡 ШАГ 2: Скачиваю аудио по URL...")
            print(f"   URL для скачивания: {audio_url[:100]}...")

            async with session.get(audio_url) as resp:
                print(f"   Ответ на скачивание: status={resp.status}")
                print(f"   Content-Type: {resp.headers.get('Content-Type', 'unknown')}")
                print(f"   Content-Length: {resp.headers.get('Content-Length', 'unknown')}")

                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"   ❌ ОШИБКА: Не удалось скачать аудио")
                    print(f"   Статус: {resp.status}")
                    print(f"   Текст: {error_text[:200]}")
                    return False

                audio_bytes = await resp.read()
                print(f"   ✅ Аудио скачано успешно!")
                print(f"   Размер: {len(audio_bytes)} байт")
                print(f"   Первые 20 байт: {audio_bytes[:20] if len(audio_bytes) > 20 else audio_bytes}")

            # ========== ШАГ 3: ЗАГРУЖАЕМ АУДИО НА СЕРВЕР ==========
            print(f"\n📡 ШАГ 3: Загружаю аудио на сервер MAX...")
            print(f"   URL загрузки: {upload_url[:80]}...")

            data = aiohttp.FormData()
            data.add_field('file', audio_bytes, filename='voice.ogg', content_type='audio/ogg')
            print(f"   FormData создан: filename='voice.ogg', content_type='audio/ogg'")

            async with session.post(upload_url, data=data) as upload_resp:
                print(f"   Ответ на загрузку: status={upload_resp.status}")

                if upload_resp.status not in (200, 201):
                    text = await upload_resp.text()
                    print(f"   ❌ ОШИБКА: Не удалось загрузить аудио")
                    print(f"   Статус: {upload_resp.status}")
                    print(f"   Текст: {text[:200]}")
                    return False

                print(f"   ✅ Аудио загружено на сервер MAX!")

            # ========== ШАГ 4: ОТПРАВЛЯЕМ СООБЩЕНИЕ С АУДИО ==========
            print(f"\n📡 ШАГ 4: Отправляю сообщение с аудио...")
            print(f"   chat_id: {chat_id}")
            print(f"   caption: {caption}")
            print(f"   new_token: {new_token[:40]}...")

            # Формируем payload для отправки
            send_url = "https://platform-api.max.ru/messages"
            attachment_obj = {
                "type": "audio",
                "payload": {"token": new_token}
            }
            payload = {
                "chat_id": chat_id,
                "text": caption,
                "attachments": [attachment_obj]
            }

            print(f"   send_url: {send_url}")
            print(f"   payload: {payload}")

            async with session.post(
                    send_url,
                    headers={"Authorization": bot_token, "Content-Type": "application/json"},
                    json=payload
            ) as resp:
                print(f"   Ответ на отправку: status={resp.status}")

                if resp.status != 200:
                    text = await resp.text()
                    print(f"   ❌ ОШИБКА: Не удалось отправить сообщение с аудио")
                    print(f"   Статус: {resp.status}")
                    print(f"   Текст: {text}")
                    return False

                result = await resp.json()
                print(f"   ✅ Аудио сообщение успешно отправлено!")
                print(f"   Ответ от сервера: {result}")

                print("\n" + "=" * 70)
                print("🎉🎉🎉 АУДИО УСПЕШНО ОТПРАВЛЕНО! 🎉🎉🎉")
                print("=" * 70)
                return True

    except aiohttp.ClientError as e:
        print(f"\n❌❌❌ СЕТЕВАЯ ОШИБКА: {e}")
        print(f"   Тип: {type(e).__name__}")
        logging.exception(f"Сетевая ошибка при отправке аудио: {e}")
        return False

    except Exception as e:
        print(f"\n❌❌❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print(f"   Тип: {type(e).__name__}")
        logging.exception(f"Критическая ошибка при отправке аудио: {e}")
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
        """
        Отправляет обратно полученное сообщение.
        Для аудио использует скачивание и повторную загрузку через InputMediaBuffer.
        """

        ctx = await EventContext.from_event(event)
        ctx.log_info("format_received_message ВЫЗВАНА")

        message = event.message
        text = message.body.text or ""
        attachments = message.body.attachments or []
        chat_id = message.recipient.chat_id

        # Формируем базовый ответ
        now = datetime.now()
        response = (
            f"✅ Получено сообщение!\n"
            f"📅 {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"👤 Отправитель: {user_name} (ID: {user_id})\n"
        )

        if text:
            response += f"📝 Текст:\n{text}\n"

        if not attachments:
            await event.message.answer(response)
            await context.set_state(None)
            return

        # Обрабатываем вложения
        att_types = []
        has_audio = False
        audio_url = None
        attachments_for_send = []

        for att in attachments:
            att_type = att.type.lower() if att.type else "неизвестно"
            att_types.append(att_type)
            ctx.log_info(f"  - тип: {att_type}")

            if att_type == "audio" and hasattr(att, 'payload') and att.payload:
                has_audio = True
                audio_url = getattr(att.payload, 'url', None)
                ctx.log_info(f"    аудио URL: {audio_url[:80] if audio_url else 'None'}...")

        response += f"📎 Вложения: {', '.join(att_types)}\n"

        # Если есть аудио, обрабатываем его отдельно
        if has_audio and audio_url:
            ctx.log_info(f"Скачиваю аудио по URL: {audio_url[:50]}...")

            # Показываем индикатор "отправляет файл"
            from maxapi.enums.sender_action import SenderAction
            await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)

            try:
                import aiohttp
                from maxapi.types.input_media import InputMediaBuffer

                # Скачиваем аудио
                async with aiohttp.ClientSession() as session:
                    async with session.get(audio_url) as resp:
                        if resp.status == 200:
                            audio_data = await resp.read()
                            ctx.log_info(f"✅ Аудио скачано: {len(audio_data)} байт")

                            # Создаём вложение через InputMediaBuffer
                            media = InputMediaBuffer(
                                buffer=audio_data,
                                filename="voice_message.ogg"
                            )
                            attachments_for_send.append(media)
                            ctx.log_info("✅ Аудио добавлено в attachments_for_send")
                        else:
                            ctx.log_info(f"❌ Ошибка скачивания: {resp.status}")
                            response += f"\n⚠️ Не удалось скачать аудио (статус: {resp.status})"
            except Exception as e:
                ctx.log_info(f"❌ Ошибка при обработке аудио: {e}")
                response += f"\n⚠️ Ошибка при обработке аудио: {e}"

        # Отправляем ОДНО сообщение с текстом и всеми вложениями
        try:
            if attachments_for_send:
                await bot.send_message(
                    chat_id=chat_id,
                    text=response,
                    attachments=attachments_for_send
                )
                ctx.log_info(f"✅ Сообщение отправлено через send_message (вложений: {len(attachments_for_send)})")
            else:
                await event.message.answer(response)
                ctx.log_info("Текстовый ответ отправлен")
        except Exception as e:
            ctx.log_info(f"❌ Ошибка при отправке: {e}")
            await event.message.answer(response + f"\n\n⚠️ Не удалось отправить вложения: {e}")

        # Сбрасываем состояние
        ctx.log_info("Сброс состояния waiting_for_message")
        await context.set_state(None)
        await context.set_data({})

        ctx.log_info("format_received_message ЗАВЕРШЕНА")


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


