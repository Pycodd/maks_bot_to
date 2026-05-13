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
        Использует forward() для любых вложений (аудио, фото, видео, файлы).
        """

        print("\n" + "=" * 80)
        print("🔵🔵🔵 format_received_message НАЧАЛО 🔵🔵🔵")
        print(f"   Время: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print(f"   user_name: {user_name}")
        print(f"   user_id: {user_id}")
        print("=" * 80)

        message = event.message
        text = message.body.text or ""
        attachments = message.body.attachments or []
        chat_id = message.recipient.chat_id

        print(f"📋 Параметры сообщения:")
        print(f"   chat_id: {chat_id}")
        print(f"   text длина: {len(text)} символов")
        print(f"   text содержание: '{text[:100] if text else 'пусто'}'")
        print(f"   количество вложений: {len(attachments)}")

        # Формируем текстовый ответ
        now = datetime.now()
        response = (
            f"✅ Получено сообщение!\n"
            f"📅 {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"👤 Отправитель: {user_name} (ID: {user_id})\n"
        )

        if text:
            response += f"📝 Текст:\n{text}\n"
            print(f"📝 Добавлен текст в ответ: '{text[:50]}...'")

        if attachments:
            print(f"\n📎 ОБРАБОТКА ВЛОЖЕНИЙ (всего: {len(attachments)})")

            # Определяем типы вложений
            att_types = []
            for idx, att in enumerate(attachments):
                att_type = att.type.lower() if att.type else "неизвестно"
                att_types.append(att_type)

                print(f"   Вложение #{idx + 1}:")
                print(f"      тип: {att_type}")

                if hasattr(att, 'payload') and att.payload:
                    print(f"      payload: {att.payload}")
                    token = getattr(att.payload, 'token', None)
                    url = getattr(att.payload, 'url', None)
                    if token:
                        print(f"      token: {token[:50] if len(token) > 50 else token}...")
                    if url:
                        print(f"      url: {url[:80] if len(url) > 80 else url}...")
                    if att_type == "audio":
                        duration = getattr(att.payload, 'duration', None)
                        print(f"      duration: {duration} сек.")
                else:
                    print(f"      НЕТ PAYLOAD")

            response += f"📎 Вложения: {', '.join(att_types)}\n"
            print(f"\n📎 Строка типов: {', '.join(att_types)}")

            # ПЕРЕСЫЛАЕМ ОРИГИНАЛЬНОЕ СООБЩЕНИЕ (работает для любых вложений!)
            print(f"\n🔄 ПЕРЕСЫЛКА СООБЩЕНИЯ...")
            print(f"   from chat: {chat_id}")
            print(f"   to chat: {chat_id}")

            try:
                forward_result = await event.message.forward(chat_id=chat_id)
                print(f"   ✅ forward() выполнен успешно!")
                print(f"   Результат: {forward_result}")
                response += "🔄 Сообщение переслано.\n"
            except Exception as e:
                print(f"   ❌❌❌ ОШИБКА ПРИ forward() ❌❌❌")
                print(f"   Тип ошибки: {type(e).__name__}")
                print(f"   Текст ошибки: {e}")
                response += f"⚠️ Не удалось переслать вложения: {e}\n"
        else:
            print(f"\n📎 НЕТ ВЛОЖЕНИЙ (только текст)")
            response += "📎 Нет вложений\n"

        # Отправляем текстовый ответ
        print(f"\n📤 ОТПРАВКА ТЕКСТОВОГО ОТВЕТА...")
        print(f"   Длина ответа: {len(response)} символов")
        print(f"   Содержание:\n{response[:300]}{'...' if len(response) > 300 else ''}")

        try:
            await event.message.answer(response)
            print(f"   ✅ Текстовый ответ отправлен успешно!")
        except Exception as e:
            print(f"   ❌ Ошибка при отправке текстового ответа: {e}")
            try:
                await event.message.answer("⚠️ Произошла ошибка при формировании ответа.")
            except:
                pass

        # Сбрасываем состояние
        print(f"\n🔄 СБРОС СОСТОЯНИЯ...")
        try:
            await context.set_state(None)
            await context.set_data({})
            print(f"   ✅ Состояние сброшено")
        except Exception as e:
            print(f"   ❌ Ошибка при сбросе состояния: {e}")

        print("\n" + "=" * 80)
        print("🔵🔵🔵 format_received_message ЗАВЕРШЕНА 🔵🔵🔵")
        print("=" * 80 + "\n")


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


