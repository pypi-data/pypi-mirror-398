import os


def get_env_variable(var_name, required=True):
    """
    Retrieves the value of an environment variable and performs validation.
    :param var_name: Name of the environment variable.
    :param required: If True, raises an error if the variable is not set.
    :return: The value of the environment variable (or None if not required and not set).
    :raises EnvironmentError: If the variable is required but not set.
    """
    value = os.environ.get(var_name)

    if required and not value:
        raise EnvironmentError(f"Environment variable '{var_name}' is not set.")

    return value


# def execution_notifier(func):
#     bot = telegram.Bot(token=os.environ.get("TELEGRAM_BOBR_BOT_TOKEN"))
#
#     async def wrapper(*args, **kwargs):
#         try:
#             result = await func(*args, **kwargs)
#             await bot.send_message(
#                 chat_id=-1002181072995,
#                 text="✅The process <b>getx_slack_report</b> has been completed successfully",
#                 disable_notification=True,
#                 parse_mode=ParseMode.HTML
#             )
#             return result
#         except Exception as e:
#             await bot.send_message(
#                 chat_id=-1002181072995,
#                 text="🆘The process <b>getx_slack_report</b> has failed",
#                 parse_mode=ParseMode.HTML
#             )
#             raise
#
#     return wrapper