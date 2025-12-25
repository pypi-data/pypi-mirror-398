from loguru import logger


def configure_logger():
    logger.remove()

    # Format
    console_format = "<green>{time:HH:mm:ss}</green> | " "<level>{level}</level> >> " "{message}"

    # Terminal logging
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format=console_format,
        colorize=True,
    )

    # File logging
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="10 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        compression="zip",
    )

    return logger


configure_logger()
