import asyncio

from airflow.notifications.basenotifier import BaseNotifier
from telegram import Bot
from telegram.constants import ParseMode

from dump.config_utils import load_config


def send_telegram_message_sync(
    token: str,
    chat_id: str,
    message: str,
    parse_mode: str = "Markdown",
    disable_notification: bool = False,
) -> None:

    async def _send_async():
        bot = Bot(token=token)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )

    # Пытаемся использовать существующий event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Если loop уже запущен, используем nest_asyncio
    if loop.is_running():
        loop.create_task(_send_async())
    else:
        loop.run_until_complete(_send_async())


class TelegramNotification(BaseNotifier):
    def __init__(
        self,
        tg_notification_config_name: str = "tg_notification.ini",
        tg_notification_config_section: str = "default",
    ):
        self.__config = load_config(
            filename=tg_notification_config_name,
            section=tg_notification_config_section,
        )

    def notify(self, context):
        telegram_bot_token, telegram_chat_id, airflow_url = self.__config.values()

        task_id = context["ti"].task_id.replace("_", "\_")
        task_state = context["ti"].state.replace("_", "\_")
        task_log_url = (
            context["ti"]
            .log_url.replace("http://localhost:8080", airflow_url)
            .replace("_", "\_")
        )
        dag_name = context["ti"].dag_id.replace("_", "\_")

        message_template = (
            f"***Dag name:*** {dag_name} \n"
            f"***Task id:*** {task_id} \n"
            f"***Task State:*** \N{Cross mark}{task_state}\N{Cross mark} \n"
            f"***Task Log URL:*** {task_log_url} \n"
        )

        send_telegram_message_sync(
            token=telegram_bot_token,
            chat_id=telegram_chat_id,
            message=message_template,
        )


class TelegramNotificationMixin:
    def __init__(
        self,
        tg_notification_config_name: str = "tg_notification.ini",
        tg_notification_config_section: str = "default",
        *args,
        **kwargs,
    ):
        self.__config = load_config(
            filename=tg_notification_config_name,
            section=tg_notification_config_section,
            *args,
            **kwargs,
        )

    def notify(self, message: str):
        telegram_bot_token, telegram_chat_id, _ = self.__config.values()

        send_telegram_message_sync(
            token=telegram_bot_token,
            chat_id=telegram_chat_id,
            message=message,
        )
