from imports import (MessageCreated, Audio, Video, Image, File, Sticker, Location, Contact, AttachmentUpload,
                     Keyboards, AttachmentPayload, UploadType, pytz, MemoryContext, SenderAction, aiohttp,
                     InputMediaBuffer, datetime, EventContext)


# Импорты для работы с VCF
try:
    from maxapi.utils.vcf import parse_vcf_info
    _has_vcf_parser = True
except ImportError:
    _has_vcf_parser = False

TZ_VOLGOGRAD = pytz.timezone('Europe/Volgograd')


class MessageHandlers:
    """
    Класс для обработки входящих сообщений.
    Поддерживает фото, видео, аудио, файлы, геолокацию.
    Контакты не обрабатываются.
    """

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
        Поддерживает фото, видео, аудио, файлы, геолокацию.
        Контакты не обрабатываются.
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

        default_kb = Keyboards.main_menu_keyboard()
        now = datetime.now(TZ_VOLGOGRAD)

        response = await MessageHandlers._build_base_response(
            user_name=user_name,
            user_id=user_id,
            now=now,
            text=text
        )

        if not attachments:
            await event.message.answer(response, attachments=[default_kb])
            await context.set_state(None)
            return

        # Обрабатываем вложения
        result = await MessageHandlers._process_attachments(attachments, ctx)

        response += f"📎 Вложения: {', '.join(result['attachment_types'])}\n"

        # Отправляем в зависимости от типа вложения
        if result['location_data']:
            await MessageHandlers._handle_location(
                event=event,
                bot=bot,
                chat_id=chat_id,
                response=response,
                location_data=result['location_data'],
                now=now,
                default_kb=default_kb
            )
        elif result['need_download'] and result['audio_url']:
            await MessageHandlers._handle_audio(
                event=event,
                bot=bot,
                chat_id=chat_id,
                response=response,
                audio_url=result['audio_url'],
                default_kb=default_kb,
                ctx=ctx
            )
        elif result['attachments_for_send']:
            await MessageHandlers._handle_media(
                event=event,
                bot=bot,
                chat_id=chat_id,
                response=response,
                attachments_for_send=result['attachments_for_send'],
                attachment_types=result['attachment_types'],
                default_kb=default_kb,
                ctx=ctx
            )
        else:
            await event.message.answer(response)
            ctx.log_info("Текстовый ответ отправлен (вложения не обработаны)")

        # Сбрасываем состояние
        await context.set_state(None)
        await context.set_data({})
        ctx.log_info("format_received_message ЗАВЕРШЕНА")

    @staticmethod
    async def _build_base_response(user_name: str, user_id: int, now: datetime, text: str) -> str:
        """Формирует базовую часть ответа"""
        response = (
            f"✅ Получено сообщение!\n"
            f"📅 {now.strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"👤 Отправитель: {user_name} (ID: {user_id})\n"
        )
        if text:
            response += f"📝 Текст:\n{text}\n"
        return response

    @staticmethod
    async def _process_attachments(attachments: list, ctx) -> dict:
        """Обрабатывает вложения и возвращает структурированный результат"""
        result = {
            'attachments_for_send': [],
            'attachment_types': [],
            'need_download': False,
            'audio_url': None,
            'location_data': None
        }

        for att in attachments:
            if isinstance(att, Image):
                result['attachment_types'].append("фото")
                token = MessageHandlers._get_token(att)
                if token:
                    result['attachments_for_send'].append(
                        AttachmentUpload(
                            type=UploadType.IMAGE,
                            payload=AttachmentPayload(token=token)
                        )
                    )
                    ctx.log_info(f"  фото добавлено (токен: {token[:20]}...)")

            elif isinstance(att, Video):
                result['attachment_types'].append("видео")
                token = MessageHandlers._get_token(att)
                if token:
                    result['attachments_for_send'].append(
                        AttachmentUpload(
                            type=UploadType.VIDEO,
                            payload=AttachmentPayload(token=token)
                        )
                    )
                    ctx.log_info(f"  видео добавлено (токен: {token[:20]}...)")

            elif isinstance(att, Audio):
                result['attachment_types'].append("аудио")
                result['need_download'] = True
                if hasattr(att, 'payload') and att.payload:
                    result['audio_url'] = getattr(att.payload, 'url', None)
                    ctx.log_info(f"  аудио URL: {result['audio_url'][:80] if result['audio_url'] else 'None'}...")

            elif isinstance(att, File):
                result['attachment_types'].append("файл")
                token = MessageHandlers._get_token(att)
                if token:
                    result['attachments_for_send'].append(
                        AttachmentUpload(
                            type=UploadType.FILE,
                            payload=AttachmentPayload(token=token)
                        )
                    )
                    ctx.log_info(f"  файл добавлено (токен: {token[:20]}...)")

            elif isinstance(att, Location):
                result['attachment_types'].append("геолокация")
                result['location_data'] = await MessageHandlers._process_location(att, ctx)

            elif isinstance(att, Contact):
                result['attachment_types'].append("контакт (игнорирован)")
                ctx.log_info("  контакт получен, но игнорируется")

            elif isinstance(att, Sticker):
                result['attachment_types'].append("стикер")
                ctx.log_info("  стикер (пока не обрабатывается)")

            else:
                result['attachment_types'].append("неизвестно")
                ctx.log_info(f"  неизвестный тип: {type(att)}")

        return result

    @staticmethod
    def _get_token(att) -> str:
        """Получает токен из вложения"""
        if hasattr(att, 'payload') and att.payload:
            return getattr(att.payload, 'token', None)
        return None

    @staticmethod
    async def _process_location(att, ctx) -> dict:
        """Обрабатывает геолокацию и получает адрес"""
        lat = getattr(att, 'latitude', None)
        lon = getattr(att, 'longitude', None)

        if lat is None and hasattr(att, 'payload') and att.payload:
            lat = getattr(att.payload, 'latitude', None)
            lon = getattr(att.payload, 'longitude', None)

        if not lat or not lon:
            return None

        address = None
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'User-Agent': 'MAX_Bot/1.0 (https://bothost.ru)'}
                url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        address = data.get('display_name')
                        if address:
                            ctx.log_info(f"  адрес получен: {address[:80]}...")
        except Exception as e:
            ctx.log_info(f"  ошибка геокодинга: {e}")

        ctx.log_info(f"  геолокация: lat={lat}, lon={lon}")
        return {'lat': lat, 'lon': lon, 'address': address}

    @staticmethod
    async def _handle_audio(event, bot, chat_id, response, audio_url, default_kb, ctx):
        """Обрабатывает отправку аудио"""
        await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)

        try:
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
                            attachments=[media] + [default_kb]
                        )
                        ctx.log_info("✅ Аудио отправлено через InputMediaBuffer")
                    else:
                        ctx.log_info(f"❌ Ошибка скачивания аудио: {resp.status}")
                        await event.message.answer(response + "\n\n⚠️ Не удалось скачать аудио")
        except Exception as e:
            ctx.log_info(f"❌ Ошибка при обработке аудио: {e}")
            await event.message.answer(response + f"\n\n⚠️ Ошибка: {e}")

    @staticmethod
    async def _handle_media(event, bot, chat_id, response, attachments_for_send, attachment_types, default_kb, ctx):
        """Обрабатывает отправку фото, видео, файлов"""
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
                attachments=attachments_for_send + [default_kb]
            )
            ctx.log_info(f"✅ Сообщение отправлено с {len(attachments_for_send)} вложениями")
        except Exception as e:
            ctx.log_info(f"❌ Ошибка при отправке: {e}")
            await event.message.answer(response + f"\n\n⚠️ Не удалось отправить вложения: {e}")

    @staticmethod
    async def _handle_location(event, bot, chat_id, response, location_data, now, default_kb):
        """Обрабатывает отправку геолокации"""
        lat = location_data.get('lat')
        lon = location_data.get('lon')
        address = location_data.get('address')

        response += f"\n📍 **Геолокация:**\n"
        if address:
            response += f"   🏠 Адрес: {address}\n"
        else:
            response += f"   🏠 Адрес: не удалось определить\n"
        response += f"   📐 Координаты: {lat}, {lon}\n"
        response += f"   🗺️ Google Maps: https://www.google.com/maps?q={lat},{lon}\n"
        response += f"   🗺️ Яндекс.Карты: https://yandex.ru/maps/?pt={lon},{lat}&z=15&l=map\n"
        response += f"   ⏱️ Время получения: {now.strftime('%H:%M:%S')}\n"

        await bot.send_action(chat_id=chat_id, action=SenderAction.SENDING_FILE)
        await event.message.answer(response, attachments=[default_kb])