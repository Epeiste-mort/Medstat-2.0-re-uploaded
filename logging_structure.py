import logging

class Stream_Handling:
    @staticmethod
    def stream_handler_setup():
        stream_handler = logging.StreamHandler() 
        stream_handler.setLevel(logging.INFO)
        log_formatter = logging.Formatter(r"%(asctime)s:%(name)s:%(levelname)s-%(message)s")
        stream_handler.setFormatter(log_formatter)
        return stream_handler
    
    STREAM_HANDLER = stream_handler_setup()

def logger_creation(main_logger: bool = False, module_name: str = None, save_logger: bool = False, alternative_name: str = None):
    if not hasattr(logger_creation, 'logger_dict'):  # Проверяем, был ли уже создан словарь
        logger_creation.logger_dict = {}

    def logger_setup(module_name):
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.INFO)
        log_handler = logging.FileHandler(filename=f"logs\\{module_name}.log", mode="a", encoding="utf-8") if alternative_name == None else logging.FileHandler(filename=f"logs\\{alternative_name}.log", mode="a", encoding="utf-8")
        log_formatter = logging.Formatter(r"%(asctime)s:%(name)s:%(levelname)s-%(message)s")
        log_handler.setFormatter(log_formatter)
        logger.addHandler(log_handler)
        return logger

    def logger_keeper(logger = None):
        if logger:
            logger_creation.logger_dict.update([(logger.name, logger)])
        else:
            pass
        yield logger_creation.logger_dict

    if main_logger == True:
        return logger_setup(module_name if module_name else alternative_name)

    if save_logger == True:
        logger = logger_setup(module_name=module_name)
        next(logger_keeper(logger=logger))
        return logger
    else:
        return next(logger_keeper())

def logger_handling(handler_to_add, logger_to_recieve):
    logger_to_recieve.addHandler(handler_to_add)
    return logger_to_recieve
