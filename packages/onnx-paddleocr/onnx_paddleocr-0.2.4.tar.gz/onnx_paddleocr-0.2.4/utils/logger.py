import logging


def get_logger(name, level=logging.DEBUG, fmt=logging.Formatter("%(message)s")):
    root_logger = logging.getLogger()
    root_level = root_logger.level if root_logger.level != 0 else logging.NOTSET

    # 如果 root 的 level 已设置且与传入 level 相同，则直接返回，不做本地修改
    if root_level != logging.NOTSET and level == root_level:
        return logging.getLogger(name)

    # 否则按传入 level 配置当前模块的 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果没有 StreamHandler，则添加一个，保证有输出目的地
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        # fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    # 禁止传播到父 logger，避免被父 handler 过滤或重复输出
    logger.propagate = False
    return logger
