from imports import (MessageCallback, MessageCreated, Audio, Video, Image,
                     File, Sticker, Location, Contact, AttachmentUpload,Keyboards,
                     AttachmentPayload, UploadType, asyncio, pytz)
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


# Импорты для работы с VCF
try:
    from maxapi.utils.vcf import parse_vcf_info
    _has_vcf_parser = True
except ImportError:
    _has_vcf_parser = False

TZ_VOLGOGRAD = pytz.timezone('Europe/Volgograd')

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

    # @staticmethod
    # async def format_received_message(
    #         event: MessageCreated,
    #         context: MemoryContext,
    #         user_name: str,
    #         user_id: int,
    #         bot
    # ):
    #     """
    #     Отправляет обратно полученное сообщение.
    #     Поддерживает фото, видео, аудио, файлы, геолокацию.
    #     Контакты не обрабатываются.
    #     """
    #
    #     ctx = await EventContext.from_event(event)
    #     ctx.log_info("format_received_message ВЫЗВАНА")
    #
    #     body = event.message.body
    #     text = body.text or ""
    #     attachments = body.attachments if body else []
    #     chat_id = event.message.recipient.chat_id
    #
    #     if not attachments and not text:
    #         await context.set_state(None)
    #         return
    #     default_kb = Keyboards.main_menu_keyboard()
    #     now = datetime.now(TZ_VOLGOGRAD)
    #     response = (
    #         f"✅ Получено сообщение!\n"
    #         f"📅 {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
    #         f"👤 Отправитель: {user_name} (ID: {user_id})\n"
    #     )
    #
    #     if text:
    #         response += f"📝 Текст:\n{text}\n"
    #
    #     if not attachments:
    #         await event.message.answer(response, attachments=[default_kb])
    #         await context.set_state(None)
    #         return
    #
    #     attachments_for_send = []
    #     attachment_types = []
    #     need_download = False
    #     audio_url = None
    #     location_data = None
    #
    #     for att in attachments:
    #         if isinstance(att, Image):
    #             attachment_types.append("фото")
    #             if hasattr(att, 'payload') and att.payload:
    #                 token = getattr(att.payload, 'token', None)
    #                 if token:
    #                     from maxapi.types.attachments.upload import AttachmentUpload, AttachmentPayload
    #                     from maxapi.enums.upload_type import UploadType
    #                     attachments_for_send.append(
    #                         AttachmentUpload(
    #                             type=UploadType.IMAGE,
    #                             payload=AttachmentPayload(token=token)
    #                         )
    #                     )
    #                     ctx.log_info(f"  фото добавлено (токен: {token[:20]}...)")
    #
    #         elif isinstance(att, Video):
    #             attachment_types.append("видео")
    #             if hasattr(att, 'payload') and att.payload:
    #                 token = getattr(att.payload, 'token', None)
    #                 if token:
    #                     from maxapi.types.attachments.upload import AttachmentUpload, AttachmentPayload
    #                     from maxapi.enums.upload_type import UploadType
    #                     attachments_for_send.append(
    #                         AttachmentUpload(
    #                             type=UploadType.VIDEO,
    #                             payload=AttachmentPayload(token=token)
    #                         )
    #                     )
    #                     ctx.log_info(f"  видео добавлено (токен: {token[:20]}...)")
    #
    #         elif isinstance(att, Audio):
    #             attachment_types.append("аудио")
    #             need_download = True
    #             if hasattr(att, 'payload') and att.payload:
    #                 audio_url = getattr(att.payload, 'url', None)
    #                 ctx.log_info(f"  аудио URL: {audio_url[:80] if audio_url else 'None'}...")
    #
    #         elif isinstance(att, File):
    #             attachment_types.append("файл")
    #             if hasattr(att, 'payload') and att.payload:
    #                 token = getattr(att.payload, 'token', None)
    #                 if token:
    #                     from maxapi.types.attachments.upload import AttachmentUpload, AttachmentPayload
    #                     from maxapi.enums.upload_type import UploadType
    #                     attachments_for_send.append(
    #                         AttachmentUpload(
    #                             type=UploadType.FILE,
    #                             payload=AttachmentPayload(token=token)
    #                         )
    #                     )
    #                     ctx.log_info(f"  файл добавлено (токен: {token[:20]}...)")
    #
    #         elif isinstance(att, Location):
    #             attachment_types.append("геолокация")
    #             lat = getattr(att, 'latitude', None)
    #             lon = getattr(att, 'longitude', None)
    #             if lat is None and hasattr(att, 'payload') and att.payload:
    #                 lat = getattr(att.payload, 'latitude', None)
    #                 lon = getattr(att.payload, 'longitude', None)
    #
    #             if lat and lon:
    #                 address = None
    #                 try:
    #                     import aiohttp
    #                     async with aiohttp.ClientSession() as session:
    #                         headers = {'User-Agent': 'MAX_Bot/1.0 (https://bothost.ru)'}
    #                         url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
    #                         async with session.get(url, headers=headers) as resp:
    #                             if resp.status == 200:
    #                                 data = await resp.json()
    #                                 address = data.get('display_name')
    #                                 if address:
    #                                     ctx.log_info(f"  адрес получен: {address[:80]}...")
    #                             else:
    #                                 ctx.log_info(f"  Nominatim вернул статус: {resp.status}")
    #                 except Exception as e:
    #                     ctx.log_info(f"  ошибка геокодинга: {e}")
    #
    #                 location_data = {
    #                     'lat': lat,
    #                     'lon': lon,
    #                     'address': address
    #                 }
    #                 ctx.log_info(f"  геолокация: lat={lat}, lon={lon}")
    #
    #         elif isinstance(att, Contact):
    #             attachment_types.append("контакт (игнорирован)")
    #             ctx.log_info(f"  контакт получен, но игнорируется")
    #
    #         elif isinstance(att, Sticker):
    #             attachment_types.append("стикер")
    #             ctx.log_info(f"  стикер (пока не обрабатывается)")
    #         else:
    #             attachment_types.append("неизвестно")
    #             ctx.log_info(f"  неизвестный тип: {type(att)}")
    #
    #     response += f"📎 Вложения: {', '.join(attachment_types)}\n"
    #
    #     # ========== ГЕОЛОКАЦИЯ ==========
    #     if location_data:
    #         lat = location_data.get('lat')
    #         lon = location_data.get('lon')
    #         address = location_data.get('address')
    #
    #         response += f"\n📍 **Геолокация:**\n"
    #         if address:
    #             response += f"   🏠 Адрес: {address}\n"
    #         else:
    #             response += f"   🏠 Адрес: не удалось определить\n"
    #         response += f"   📐 Координаты: {lat}, {lon}\n"
    #
    #         google_maps = f"https://www.google.com/maps?q={lat},{lon}"
    #         yandex_maps = f"https://yandex.ru/maps/?pt={lon},{lat}&z=15&l=map"
    #         response += f"   🗺️ Google Maps: {google_maps}\n"
    #         response += f"   🗺️ Яндекс.Карты: {yandex_maps}\n"
    #
    #         response += f"   ⏱️ Время получения: {now.strftime('%H:%M:%S')}\n"
    #
    #     # ========== АУДИО ==========
    #     if need_download and audio_url:
    #         await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)
    #
    #         try:
    #             import aiohttp
    #             from maxapi.types.input_media import InputMediaBuffer
    #
    #             async with aiohttp.ClientSession() as session:
    #                 async with session.get(audio_url) as resp:
    #                     if resp.status == 200:
    #                         audio_data = await resp.read()
    #                         ctx.log_info(f"✅ Аудио скачано: {len(audio_data)} байт")
    #
    #                         media = InputMediaBuffer(
    #                             buffer=audio_data,
    #                             filename="voice_message.ogg"
    #                         )
    #
    #                         await bot.send_message(
    #                             chat_id=chat_id,
    #                             text=response,
    #                             attachments=[media] + [default_kb]
    #                         )
    #                         ctx.log_info("✅ Аудио отправлено через InputMediaBuffer")
    #                     else:
    #                         ctx.log_info(f"❌ Ошибка скачивания аудио: {resp.status}")
    #                         await event.message.answer(response + f"\n\n⚠️ Не удалось скачать аудио")
    #         except Exception as e:
    #             ctx.log_info(f"❌ Ошибка при обработке аудио: {e}")
    #             await event.message.answer(response + f"\n\n⚠️ Ошибка: {e}")
    #
    #     # ========== ФОТО, ВИДЕО, ФАЙЛЫ ==========
    #     elif attachments_for_send:
    #         if "видео" in attachment_types:
    #             await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_VIDEO)
    #         elif "фото" in attachment_types:
    #             await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_PHOTO)
    #         else:
    #             await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)
    #
    #         try:
    #             await bot.send_message(
    #                 chat_id=chat_id,
    #                 text=response,
    #                 attachments=attachments_for_send + [default_kb]
    #             )
    #             ctx.log_info(f"✅ Сообщение отправлено с {len(attachments_for_send)} вложениями")
    #         except Exception as e:
    #             ctx.log_info(f"❌ Ошибка при отправке: {e}")
    #             await event.message.answer(response + f"\n\n⚠️ Не удалось отправить вложения: {e}")
    #
    #     # ========== ТОЛЬКО ГЕОЛОКАЦИЯ ==========
    #     elif location_data:
    #         await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)
    #         await event.message.answer(response, attachments=[default_kb])
    #         ctx.log_info("Ответ с геолокацией отправлен")
    #
    #     else:
    #         await event.message.answer(response)
    #         ctx.log_info("Текстовый ответ отправлен (вложения не обработаны)")
    #
    #     # Сбрасываем состояние
    #     ctx.log_info("Сброс состояния waiting_for_message")
    #     await context.set_state(None)
    #     await context.set_data({})
    #
    #     ctx.log_info("format_received_message ЗАВЕРШЕНА")


# class CallbackHandlers:
#     """
#     Класс для обработки всех callback-запросов от кнопок.
#     """
#
#     async def handle(self, callback: MessageCallback, context: MemoryContext = None):
#         """
#         Главный метод-диспетчер.
#         Определяет, какой метод вызвать в зависимости от payload.
#         """
#         ctx = await EventContext.from_event(callback)
#         data = callback.callback.payload
#         ctx.log_info(f"нажал кнопку: {data}")
#
#         if data == "settings":
#             await self.settings(callback, ctx)
#         elif data == "about":
#             await self.about(callback, ctx)
#         elif data == "write_message":
#             await self.write_message(callback, ctx, context)
#         else:
#             await self.unknown(callback, ctx)
#
#     @staticmethod
#     async def settings(callback: MessageCallback, ctx: EventContext):
#         """Обработчик кнопки 'Настройки'."""
#         response = BotResponses.settings()
#         await callback.message.answer(response)
#         log_response_detailed(chat_id=ctx.chat_id, response_text=response)
#
#     @staticmethod
#     async def about(callback: MessageCallback, ctx: EventContext):
#         """Обработчик кнопки 'О боте'."""
#         response = BotResponses.about()
#         await callback.message.answer(response)
#         log_response_detailed(chat_id=ctx.chat_id, response_text=response)
#
#     @staticmethod
#     async def unknown(callback: MessageCallback, ctx: EventContext):
#         """Обработчик неизвестных колбэков."""
#         response = BotResponses.unknown()
#         await callback.message.answer(response)
#         log_response_detailed(chat_id=ctx.chat_id, response_text=response)
#
#     @staticmethod
#     async def write_message(callback: MessageCallback, ctx: EventContext, context: MemoryContext = None):
#         """Обработчик кнопки: Написать сообщение."""
#
#         if context:
#             await context.set_state(WaitingStates.waiting_for_message)
#             await context.set_data({})
#             ctx.log_info("Установлено состояние waiting_for_message")
#
#         response = BotResponses.write_message()
#         await callback.message.answer(response)
#         log_response_detailed(chat_id=ctx.chat_id, response_text=response)


