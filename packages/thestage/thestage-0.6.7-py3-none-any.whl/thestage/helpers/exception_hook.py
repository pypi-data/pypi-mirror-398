import sys
import traceback

from thestage.helpers.logger.app_logger import app_logger


def exception_handler(exception_type, exception, tb):
    print(exception)
    tb_list = traceback.format_exception(exception_type, exception, tb)
    tb_text = ''.join(tb_list)
    app_logger.error(tb_text)


sys.excepthook = exception_handler
