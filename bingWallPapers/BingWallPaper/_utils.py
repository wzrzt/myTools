

import os
import logging


def set_logger(app_name='logger', log_dir='logs', silent=False):
    logger = logging.getLogger(app_name)
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
        logger.info("Directory %s doesnot exist, will be created." % (log_dir,))
    else:
        logger.info("Directory %s is already there" % (log_dir))

    # %(levelname)8s 右对齐 %(levelname)-8s 左对齐 
    # formatter = logging.Formatter(fmt='%(name)s-[%(levelname)8s]-[%(asctime)s] - %(message)s',
    #                             datefmt='%Y-%m-%d %H:%M:%S')

    formatter = logging.Formatter('{asctime}-{name}-[{levelname:^8s}] - {message}', style='{',  datefmt='%Y-%m-%d %H:%M:%S')

    handler = logging.FileHandler(
        "{0}/{1}.log".format(log_dir, app_name),
        mode='a', encoding='utf-8')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    if silent:
        pass
    else:
        log_file_handler = logging.StreamHandler()
        log_file_handler.setLevel(logging.INFO)
        log_file_handler.setFormatter(formatter)
        logger.addHandler(log_file_handler)

    return logger