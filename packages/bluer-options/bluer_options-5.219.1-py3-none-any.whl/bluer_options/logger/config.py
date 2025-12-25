import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
from bluer_options.env import bluer_ai_log_filename

# to hide "botocore.credentials Found credentials in environment variables."
logging.getLogger("botocore.credentials").setLevel(logging.WARNING)


# Based on https://stackoverflow.com/a/22313803
logging.addLevelName(logging.INFO, "")
logging.addLevelName(logging.DEBUG, "❓ ")
logging.addLevelName(logging.ERROR, "❗️ ")
logging.addLevelName(logging.WARNING, "⚠️  ")

logging_level = logging.INFO

logging.getLogger().setLevel(logging_level)

log_formatter = logging.Formatter("%(levelname)s%(name)s %(message)s")
try:
    file_handler = RotatingFileHandler(
        bluer_ai_log_filename,
        maxBytes=10485760,
        backupCount=10000,
    )
    file_handler.setLevel(logging_level)
    file_handler.setFormatter(log_formatter)
    logging.getLogger().addHandler(file_handler)
except:
    pass

console_handler = logging.StreamHandler()
console_handler.setLevel(logging_level)
console_handler.setFormatter(log_formatter)
logging.getLogger().addHandler(console_handler)


def get_logger(ICON) -> Logger:
    return logging.getLogger(f"{ICON} ")


logger = get_logger("::")


# https://stackoverflow.com/a/10645855
def crash_report(description):
    logger.error(f"crash: {description}", exc_info=1)


def shorten_text(
    text: str,
    max_length: int = 100,
) -> str:
    return (
        "{}...".format(
            text[: max_length - 3],
        )
        if len(text) > max_length
        else text
    )


def log_long_text(
    logger: Logger,
    text: str,
    max_length: int = 100,
):
    logger.info(
        "{:,} char(s): {}".format(
            len(text),
            shorten_text(
                text=text,
                max_length=max_length,
            ),
        )
    )


def log_dict(
    logger: Logger,
    title: str,
    dict_of_items: dict,
    item_name_plural: str = "item(s)",
    max_count: int = 5,
    max_length: int = 100,
):
    logger.info(f"{title} {len(dict_of_items)} {item_name_plural}.")

    for index, (item, info) in enumerate(dict_of_items.items()):
        logger.info(
            "#{: 4} - {}: {}{}".format(
                index,
                item,
                info if max_length == -1 else info[:max_length],
                "..." if len(info) > max_length else "",
            )
        )

        if max_count != -1 and index > max_count:
            logger.info("...")
            break


def log_list_as_str(
    title: str,
    list_of_items: list,
    item_name_plural: str = "item(s)",
    max_count: int = 5,
) -> str:
    return "{} {} {}: {}".format(
        title,
        len(list_of_items),
        item_name_plural,
        ", ".join(
            list_of_items
            if max_count == -1
            else (
                list_of_items[:max_count]
                + (["..."] if len(list_of_items) > max_count else [])
            )
        ),
    )


def log_list(
    logger: Logger,
    title: str,
    list_of_items: list,
    item_name_plural: str = "item(s)",
    max_count: int = 5,
    max_length: int = 100,
    itemize: bool = True,
):
    if not itemize:
        logger.info(
            log_list_as_str(
                title=title,
                list_of_items=list_of_items,
                item_name_plural=item_name_plural,
                max_count=max_count,
            )
        )
        return

    logger.info(f"{title} {len(list_of_items)} {item_name_plural}")

    for index, item in enumerate(list_of_items):
        logger.info(
            "#{: 4} - {}{}".format(
                index,
                item if max_length == -1 else item[:max_length],
                "" if max_length == -1 else "..." if len(item) > max_length else "",
            )
        )

        if max_count != -1 and index >= max_count - 1:
            logger.info("...")
            break
