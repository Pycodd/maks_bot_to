from imports import (Audio, Video, Image, File, Sticker, Location, Contact, AttachmentUpload,
                     AttachmentPayload, UploadType, pytz, SenderAction, aiohttp,
                     InputMediaBuffer, datetime, TextFormat, logging, EditedMessage)


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
            response: str,
            bot,
            user_id: int,
            chat_id: int,
            chat_type: str = None,
            attachments: list = None,
            keyboard=None,
            text_format=None
    ):
        """
        Отправляет сообщение с поддержкой вложений.

        Args:
            response: Текст сообщения (обязательный)
            bot: Экземпляр бота
            user_id: ID пользователя (обязательный)
            chat_id: ID чата (обязательный)
            chat_type: Тип чата (необязательный)
            attachments: Список вложений (опционально)
            keyboard: Клавиатура (опционально)
            text_format: Формат текста (HTML/MARKDOWN)
        """
        logging.info(f"format_received_message ВЫЗВАНА | user: {user_id} | chat: {chat_id} | type: {chat_type}")

        now = datetime.now(TZ_VOLGOGRAD)

        if attachments:
            result = await MessageHandlers._process_attachments(
                attachments=attachments
            )

            response += f"📎 Вложения: {', '.join(result['attachment_types'])}\n"

            if result['location_data']:
                await MessageHandlers._handle_location(
                    bot=bot,
                    user_id=user_id,
                    chat_id=chat_id,
                    response=response,
                    location_data=result['location_data'],
                    now=now,
                    keyboard=keyboard,
                    text_format=text_format
                )

                logging.info("format_received_message ЗАВЕРШЕНА")
                return

            elif result['need_download'] and result['audio_url']:
                await MessageHandlers._handle_audio(
                    bot=bot,
                    user_id=user_id,
                    chat_id=chat_id,
                    response=response,
                    audio_url=result['audio_url'],
                    keyboard=keyboard,
                    text_format=text_format
                )

                logging.info("format_received_message ЗАВЕРШЕНА")
                return

            elif result['attachments_for_send']:
                await MessageHandlers._handle_media(
                    bot=bot,
                    user_id=user_id,
                    chat_id=chat_id,
                    response=response,
                    attachments_for_send=result['attachments_for_send'],
                    attachment_types=result['attachment_types'],
                    keyboard=keyboard,
                    text_format=text_format
                )

                logging.info("format_received_message ЗАВЕРШЕНА")
                return

        attachments_list = [keyboard] if keyboard else []
        await bot.send_message(
            user_id=user_id,
            chat_id=chat_id,
            text=response,
            attachments=attachments_list,
            format=text_format
        )

        logging.info("format_received_message ЗАВЕРШЕНА")

    @staticmethod
    async def _process_attachments(attachments: list) -> dict:
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
                    logging.info(f"  фото добавлено (токен: {token[:20]}...)")

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
                    logging.info(f"  видео добавлено (токен: {token[:20]}...)")

            elif isinstance(att, Audio):
                result['attachment_types'].append("аудио")
                result['need_download'] = True
                if hasattr(att, 'payload') and att.payload:
                    result['audio_url'] = getattr(att.payload, 'url', None)
                    logging.info(f"  аудио URL: {result['audio_url'][:80] if result['audio_url'] else 'None'}...")

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
                    logging.info(f"  файл добавлено (токен: {token[:20]}...)")

            elif isinstance(att, Location):
                result['attachment_types'].append("геолокация")
                result['location_data'] = await MessageHandlers._process_location(att)

            elif isinstance(att, Contact):
                result['attachment_types'].append("контакт (игнорирован)")
                logging.info("  контакт получен, но игнорируется")

            elif isinstance(att, Sticker):
                result['attachment_types'].append("стикер")
                logging.info("  стикер (пока не обрабатывается)")

            else:
                result['attachment_types'].append("неизвестно")
                logging.info(f"  неизвестный тип: {type(att)}")

        return result

    @staticmethod
    def _get_token(att) -> str:
        """Получает токен из вложения"""
        if hasattr(att, 'payload') and att.payload:
            return getattr(att.payload, 'token', None)
        return None

    @staticmethod
    async def _process_location(att) -> dict:
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
                url = (f"https://nominatim.openstreetmap.org/reverse?format=json&lat="
                       f"{lat}&lon={lon}&zoom=18&addressdetails=1")
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        address = data.get('display_name')
                        if address:
                            logging.info(f"  адрес получен: {address[:80]}...")
        except Exception as e:
            logging.info(f"  ошибка геокодинга: {e}")

        logging.info(f"  геолокация: lat={lat}, lon={lon}")
        return {'lat': lat, 'lon': lon, 'address': address}

    @staticmethod
    async def _handle_audio(
            bot,
            user_id,
            chat_id,
            response,
            audio_url,
            keyboard,
            text_format=None
    ):
        """Обрабатывает отправку аудио"""
        await bot.send_action(
            chat_id=chat_id,
            action=SenderAction.SENDING_FILE
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as resp:
                    if resp.status == 200:
                        audio_data = await resp.read()
                        logging.info(f"✅ Аудио скачано: {len(audio_data)} байт")

                        media = InputMediaBuffer(
                            buffer=audio_data,
                            filename="voice_message.ogg"
                        )

                        attachments_list = [media]
                        if keyboard:
                            attachments_list.append(keyboard)

                        await bot.send_message(
                            user_id=user_id,
                            chat_id=chat_id,
                            text=response,
                            attachments=attachments_list,
                            format=text_format
                        )
                        logging.info("✅ Аудио отправлено через InputMediaBuffer")
                    else:
                        logging.error(f"❌ Ошибка скачивания аудио: {resp.status}")
                        await bot.send_message(
                            user_id=user_id,
                            chat_id=chat_id,
                            text=response + "\n\n⚠️ Не удалось скачать аудио",
                            format=text_format
                        )
        except Exception as e:
            logging.error(f"❌ Ошибка при обработке аудио: {e}")
            await bot.send_message(
                user_id=user_id,
                chat_id=chat_id,
                text=response + f"\n\n⚠️ Ошибка: {e}",
                format=text_format
            )

    @staticmethod
    async def _handle_media(
            bot,
            user_id,
            chat_id,
            response,
            attachments_for_send,
            attachment_types,
            keyboard,
            text_format=None
    ):
        """Обрабатывает отправку фото, видео, файлов"""
        if "видео" in attachment_types:
            await bot.send_action(
                chat_id=chat_id,
                action=SenderAction.SENDING_VIDEO
            )
        elif "фото" in attachment_types:
            await bot.send_action(
                chat_id=chat_id,
                action=SenderAction.SENDING_PHOTO
            )
        else:
            await bot.send_action(
                chat_id=chat_id,
                action=SenderAction.SENDING_FILE
            )

        try:
            attachments_list = attachments_for_send.copy()
            if keyboard:
                attachments_list.append(keyboard)

            await bot.send_message(
                user_id=user_id,
                chat_id=chat_id,
                text=response,
                attachments=attachments_list,
                format=text_format
            )
            logging.info(f"✅ Сообщение отправлено с {len(attachments_for_send)} вложениями")
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке: {e}")
            await bot.send_message(
                user_id=user_id,
                chat_id=chat_id,
                text=response + f"\n\n⚠️ Не удалось отправить вложения: {e}",
                format=text_format
            )

    @staticmethod
    async def _handle_location(
            bot,
            user_id,
            chat_id,
            response,
            location_data,
            now,
            keyboard=None,
            text_format=None
    ):
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

        await bot.send_action(
            chat_id=chat_id,
            action=SenderAction.SENDING_FILE
        )

        attachments_list = [keyboard] if keyboard else []
        await bot.send_message(
            user_id=user_id,
            chat_id=chat_id,
            text=response,
            attachments=attachments_list,
            format=text_format
        )

    @staticmethod
    async def edit_message(
            bot,
            message_id: str,
            text: str | None = None,
            attachments: list | None = None,
            text_format: TextFormat | None = None,
            notify: bool | None = None,
            sleep_after_input_media: bool | None = True
    ) -> EditedMessage | None:
        """
        Редактирует существующее сообщение.

        Args:
            bot: Экземпляр бота
            message_id: ID сообщения для редактирования
            text: Новый текст (макс. 4000 символов)
            attachments: Новые вложения (опционально)
            text_format: Формат разметки (TextFormat.MARKDOWN, TextFormat.HTML)
            notify: Отправлять ли уведомление
            sleep_after_input_media: Задержка после загрузки вложений

        Returns:
            EditedMessage или None при ошибке
        """
        try:
            result = await bot.edit_message(
                message_id=message_id,
                text=text,
                attachments=attachments,
                text_format=text_format,
                notify=notify,
                sleep_after_input_media=sleep_after_input_media
            )
            if result:
                logging.info(f"✅ Сообщение {message_id} отредактировано")
            return result
        except Exception as e:
            logging.error(f"❌ Ошибка редактирования сообщения {message_id}: {e}")
            return None

    @staticmethod
    async def edit_message_text(
            bot,
            message_id: str,
            new_text: str,
            text_format: TextFormat | None = None,
            notify: bool | None = None
    ) -> EditedMessage | None:
        """
        Упрощённый метод для редактирования ТОЛЬКО текста сообщения.

        Args:
            bot: Экземпляр бота
            message_id: ID сообщения для редактирования
            new_text: Новый текст
            text_format: Формат разметки
            notify: Отправлять ли уведомление

        Returns:
            EditedMessage или None при ошибке
        """
        return await MessageHandlers.edit_message(
            bot=bot,
            message_id=message_id,
            text=new_text,
            text_format=text_format,
            notify=notify
        )

    @staticmethod
    async def edit_message_with_attachments(
            bot,
            message_id: str,
            text: str | None = None,
            attachments: list | None = None,
            text_format: TextFormat | None = None,
            notify: bool | None = None
    ) -> EditedMessage | None:
        """
        Редактирует сообщение с новыми вложениями.

        Args:
            bot: Экземпляр бота
            message_id: ID сообщения для редактирования
            text: Новый текст (опционально)
            attachments: Новые вложения
            text_format: Формат разметки
            notify: Отправлять ли уведомление

        Returns:
            EditedMessage или None при ошибке
        """
        return await MessageHandlers.edit_message(
            bot=bot,
            message_id=message_id,
            text=text,
            attachments=attachments,
            text_format=text_format,
            notify=notify
        )

    @staticmethod
    async def send_message_to_user(
            bot,
            user_id: int,  # ← обязательный
            response: str,
            chat_id: int = None,  # ← если не указан, используем user_id
            chat_type: str = None,
            attachments: list = None,
            keyboard=None,
            text_format=None
    ):
        """
        Отправляет сообщение пользователю.

        Args:
            bot: Экземпляр бота
            user_id: ID пользователя (обязательный)
            response: Текст сообщения
            chat_id: ID чата (если не указан, используется user_id)
            chat_type: Тип чата (необязательный)
            attachments: Список вложений
            keyboard: Клавиатура
            text_format: Формат текста
        """
        try:
            target_chat_id = chat_id if chat_id else user_id

            attachments_list = attachments.copy() if attachments else []
            if keyboard:
                attachments_list.append(keyboard)

            await bot.send_message(
                chat_id=target_chat_id,
                text=response,
                attachments=attachments_list,
                format=text_format
            )
            logging.info(f"✅ Сообщение отправлено пользователю {user_id} | chat: {target_chat_id} | type: {chat_type}")
        except Exception as e:
            logging.error(f"❌ Ошибка отправки сообщения пользователю {user_id}: {e}")

    @staticmethod
    async def send_message_to_chat(
            bot,
            chat_id: int,  # ← обязательный
            response: str,
            user_id: int = None,  # ← опционально
            chat_type: str = None,
            attachments: list = None,
            keyboard=None,
            text_format=None
    ):
        """
        Отправляет сообщение в чат.

        Args:
            bot: Экземпляр бота
            chat_id: ID чата (обязательный)
            response: Текст сообщения
            user_id: ID пользователя (для логирования, опционально)
            chat_type: Тип чата (необязательный)
            attachments: Список вложений
            keyboard: Клавиатура
            text_format: Формат текста
        """
        try:
            attachments_list = attachments.copy() if attachments else []
            if keyboard:
                attachments_list.append(keyboard)

            await bot.send_message(
                chat_id=chat_id,
                text=response,
                attachments=attachments_list,
                format=text_format
            )
            logging.info(f"✅ Сообщение отправлено в чат {chat_id} | user: {user_id} | type: {chat_type}")
        except Exception as e:
            logging.error(f"❌ Ошибка отправки сообщения в чат {chat_id}: {e}")

    @staticmethod
    async def send_message(
            bot,
            chat_id: int,  # ← обязательный
            response: str,
            user_id: int = None,  # ← опционально
            chat_type: str = None,
            attachments: list = None,
            keyboard=None,
            text_format=None
    ):
        """
        Универсальный метод отправки сообщения.

        Args:
            bot: Экземпляр бота
            chat_id: ID чата (обязательный)
            response: Текст сообщения
            user_id: ID пользователя (для логирования, опционально)
            chat_type: Тип чата (необязательный)
            attachments: Список вложений
            keyboard: Клавиатура
            text_format: Формат текста
        """
        try:
            attachments_list = attachments.copy() if attachments else []
            if keyboard:
                attachments_list.append(keyboard)

            await bot.send_message(
                chat_id=chat_id,
                text=response,
                attachments=attachments_list,
                format=text_format
            )
            logging.info(f"✅ Сообщение отправлено | chat: {chat_id} | user: {user_id} | type: {chat_type}")
        except Exception as e:
            logging.error(f"❌ Ошибка отправки сообщения: {e}")