from imports import (MessageCallback, MessageCreated, Audio, Video, Image,
                     File, Sticker, Location, Contact, AttachmentUpload, AttachmentPayload, UploadType, asyncio)
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


# Импорты для работы с VCF
try:
    from maxapi.utils.vcf import parse_vcf_info
    _has_vcf_parser = True
except ImportError:
    _has_vcf_parser = False


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
        Поддерживает фото, видео, аудио, файлы, геолокацию, контакты.
        """

        ctx = await EventContext.from_event(event)
        ctx.log_info("format_received_message ВЫЗВАНА")

        body = event.message.body
        text = body.text or ""
        attachments = body.attachments if body else []
        chat_id = event.message.recipient.chat_id

        if not attachments and not text:
            await context.set_state(None)
            return

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

        attachments_for_send = []
        attachment_types = []
        need_download = False
        audio_url = None
        location_data = None
        contact_data = None

        for att in attachments:
            if isinstance(att, Image):
                attachment_types.append("фото")
                if hasattr(att, 'payload') and att.payload:
                    token = getattr(att.payload, 'token', None)
                    if token:
                        from maxapi.types.attachments.upload import AttachmentUpload, AttachmentPayload
                        from maxapi.enums.upload_type import UploadType
                        attachments_for_send.append(
                            AttachmentUpload(
                                type=UploadType.IMAGE,
                                payload=AttachmentPayload(token=token)
                            )
                        )
                        ctx.log_info(f"  фото добавлено (токен: {token[:20]}...)")

            elif isinstance(att, Video):
                attachment_types.append("видео")
                if hasattr(att, 'payload') and att.payload:
                    token = getattr(att.payload, 'token', None)
                    if token:
                        from maxapi.types.attachments.upload import AttachmentUpload, AttachmentPayload
                        from maxapi.enums.upload_type import UploadType
                        attachments_for_send.append(
                            AttachmentUpload(
                                type=UploadType.VIDEO,
                                payload=AttachmentPayload(token=token)
                            )
                        )
                        ctx.log_info(f"  видео добавлено (токен: {token[:20]}...)")

            elif isinstance(att, Audio):
                attachment_types.append("аудио")
                need_download = True
                if hasattr(att, 'payload') and att.payload:
                    audio_url = getattr(att.payload, 'url', None)
                    ctx.log_info(f"  аудио URL: {audio_url[:80] if audio_url else 'None'}...")

            elif isinstance(att, File):
                attachment_types.append("файл")
                if hasattr(att, 'payload') and att.payload:
                    token = getattr(att.payload, 'token', None)
                    if token:
                        from maxapi.types.attachments.upload import AttachmentUpload, AttachmentPayload
                        from maxapi.enums.upload_type import UploadType
                        attachments_for_send.append(
                            AttachmentUpload(
                                type=UploadType.FILE,
                                payload=AttachmentPayload(token=token)
                            )
                        )
                        ctx.log_info(f"  файл добавлено (токен: {token[:20]}...)")

            elif isinstance(att, Location):
                attachment_types.append("геолокация")
                # Координаты могут быть прямо в att или в payload
                lat = getattr(att, 'latitude', None)
                lon = getattr(att, 'longitude', None)
                if lat is None and hasattr(att, 'payload') and att.payload:
                    lat = getattr(att.payload, 'latitude', None)
                    lon = getattr(att.payload, 'longitude', None)

                if lat and lon:
                    # Получаем адрес через Nominatim (OpenStreetMap)
                    address = None
                    try:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            # Nominatim требует User-Agent
                            headers = {'User-Agent': 'MAX_Bot/1.0 (https://bothost.ru)'}
                            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
                            async with session.get(url, headers=headers) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    address = data.get('display_name')
                                    if address:
                                        ctx.log_info(f"  адрес получен: {address[:80]}...")
                                else:
                                    ctx.log_info(f"  Nominatim вернул статус: {resp.status}")
                    except Exception as e:
                        ctx.log_info(f"  ошибка геокодинга: {e}")

                    location_data = {
                        'lat': lat,
                        'lon': lon,
                        'address': address
                    }
                    ctx.log_info(f"  геолокация: lat={lat}, lon={lon}")

            elif isinstance(att, Contact):
                attachment_types.append("контакт")

                name = None
                phone = None
                email = None
                user_id_contact = None

                if hasattr(att, 'payload') and att.payload:
                    # 🔥 ИЗВЛЕКАЕМ ТЕЛЕФОН ИЗ VCF
                    vcf_info = getattr(att.payload, 'vcf_info', None)
                    if vcf_info:
                        ctx.log_info(f"  VCF найден, длина: {len(vcf_info)}")
                        # Ручной парсинг VCF
                        for line in vcf_info.split('\n'):
                            if line.startswith('FN:'):
                                name = line[3:].strip()
                                ctx.log_info(f"    FN: {name}")
                            elif line.startswith('TEL;') or line.startswith('TEL:'):
                                phone = line.split(':')[-1].strip()
                                ctx.log_info(f"    TEL: {phone}")
                            elif line.startswith('EMAIL:'):
                                email = line[6:].strip()
                                ctx.log_info(f"    EMAIL: {email}")

                    # max_info (контакт пользователя MAX)
                    max_info = getattr(att.payload, 'max_info', None)
                    if max_info:
                        if not name:
                            name = getattr(max_info, 'first_name', '')
                            last_name = getattr(max_info, 'last_name', '')
                            if last_name:
                                name = f"{name} {last_name}".strip()
                        user_id_contact = getattr(max_info, 'user_id', None)
                        ctx.log_info(f"  max_info: name={name}, user_id={user_id_contact}")
                else:
                    # Если данные прямо в att
                    name = getattr(att, 'name', '')
                    phone = getattr(att, 'phone', '')
                    ctx.log_info(f"  контакт (прямой): name={name}, phone={phone}")

                contact_data = {
                    'name': name or 'Не указано',
                    'phone': phone or None,
                    'email': email,
                    'user_id': user_id_contact
                }

                ctx.log_info(
                    f"  итоговый контакт: name={contact_data['name']}, phone={contact_data['phone']}, user_id={contact_data['user_id']}")

            elif isinstance(att, Sticker):
                attachment_types.append("стикер")
                ctx.log_info(f"  стикер (пока не обрабатывается)")
            else:
                attachment_types.append("неизвестно")
                ctx.log_info(f"  неизвестный тип: {type(att)}")

        response += f"📎 Вложения: {', '.join(attachment_types)}\n"

        # ========== ГЕОЛОКАЦИЯ ==========
        if location_data:
            lat = location_data.get('lat')
            lon = location_data.get('lon')
            address = location_data.get('address')

            response += f"\n📍 **Геолокация:**\n"
            if address:
                response += f"   🏠 Адрес: {address}\n"
            else:
                response += f"   🏠 Адрес: не удалось определить\n"
            response += f"   📐 Координаты: {lat}, {lon}\n"

            # Ссылки на карты
            google_maps = f"https://www.google.com/maps?q={lat},{lon}"
            yandex_maps = f"https://yandex.ru/maps/?pt={lon},{lat}&z=15&l=map"
            response += f"   🗺️ Google Maps: {google_maps}\n"
            response += f"   🗺️ Яндекс.Карты: {yandex_maps}\n"

            response += f"   ⏱️ Время получения: {now.strftime('%H:%M:%S')}\n"

        # ========== КОНТАКТ ==========
        if contact_data:
            name = contact_data.get('name', 'Не указано')
            phone = contact_data.get('phone')
            user_id_contact = contact_data.get('user_id')

            response += f"\n📇 **Контакт:**\n"
            response += f"   👤 Имя: {name}\n"
            if phone:
                phone_str = str(phone)
                # Форматируем номер
                if len(phone_str) == 11 and phone_str.startswith('7'):
                    phone_str = f"+{phone_str}"
                response += f"   📞 Телефон: {phone_str}\n"
            else:
                response += f"   📞 Телефон: не предоставлен\n"
            if user_id_contact:
                response += f"   🆔 ID пользователя MAX: {user_id_contact}\n"
            response += f"   ⏱️ Время получения: {now.strftime('%H:%M:%S')}\n"

        # ========== АУДИО ==========
        if need_download and audio_url:
            await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)

            try:
                import aiohttp
                from maxapi.types.input_media import InputMediaBuffer

                async with aiohttp.ClientSession() as session:
                    async with session.get(audio_url) as resp:
                        if resp.status == 200:
                            audio_data = await resp.read()
                            ctx.log_info(f"✅ Аудио скачано: {len(audio_data)} байт")

                            media = InputMediaBuffer(
                                buffer=audio_data,
                                filename="voice_message.ogg"
                            )

                            await bot.send_message(
                                chat_id=chat_id,
                                text=response,
                                attachments=[media]
                            )
                            ctx.log_info("✅ Аудио отправлено через InputMediaBuffer")
                        else:
                            ctx.log_info(f"❌ Ошибка скачивания аудио: {resp.status}")
                            await event.message.answer(response + f"\n\n⚠️ Не удалось скачать аудио")
            except Exception as e:
                ctx.log_info(f"❌ Ошибка при обработке аудио: {e}")
                await event.message.answer(response + f"\n\n⚠️ Ошибка: {e}")

        # ========== ФОТО, ВИДЕО, ФАЙЛЫ ==========
        elif attachments_for_send:
            if "видео" in attachment_types:
                await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_VIDEO)
            elif "фото" in attachment_types:
                await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_PHOTO)
            else:
                await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)

            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=response,
                    attachments=attachments_for_send
                )
                ctx.log_info(f"✅ Сообщение отправлено с {len(attachments_for_send)} вложениями")
            except Exception as e:
                ctx.log_info(f"❌ Ошибка при отправке: {e}")
                await event.message.answer(response + f"\n\n⚠️ Не удалось отправить вложения: {e}")

        # ========== ТОЛЬКО ГЕОЛОКАЦИЯ/КОНТАКТ ==========
        elif location_data or contact_data:
            await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)
            await event.message.answer(response)
            ctx.log_info("Ответ с геолокацией/контактом отправлен")

        else:
            await event.message.answer(response)
            ctx.log_info("Текстовый ответ отправлен (вложения не обработаны)")

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


