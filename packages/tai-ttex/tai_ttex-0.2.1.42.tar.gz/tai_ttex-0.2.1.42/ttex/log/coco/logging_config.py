def get_coco_logging_config(
    trigger_nth: int = 2,
    logger_name: str = "coco_logger",
    disable_existing: bool = False,
) -> dict:
    config_dict = {
        "version": 1,
        "disable_existing_loggers": disable_existing,
        "formatters": {
            "info_form": {
                "()": "ttex.log.coco.KeyFormatter",
                "key": "info",
            },
            "log_dat_form": {
                "()": "ttex.log.coco.KeyFormatter",
                "key": "log_dat",
            },
            "log_tdat_form": {
                "()": "ttex.log.coco.KeyFormatter",
                "key": "log_tdat",
            },
        },
        "filters": {
            "info_filter": {
                "()": "ttex.log.coco.KeyFilter",
                "key": "info",
            },
            "log_dat_filter": {
                "()": "ttex.log.coco.KeyFilter",
                "key": "log_dat",
            },
            "log_tdat_filter": {
                "()": "ttex.log.coco.KeyFilter",
                "key": "log_tdat",
            },
            "coco_filter": {
                "()": "ttex.log.coco.EventKeysplitFilter",
                "key_splitter_cls": "ttex.log.coco.COCOKeySplitter",
                "key_splitter_args": {"trigger_nth": trigger_nth},
            },
        },
        "handlers": {
            "info_handler": {
                "()": "ttex.log.coco.ManualRotatingFileHandler",
                "filepath": "coco_info.txt",
                "key": "info",
                "mode": "a",
                "formatter": "info_form",
                "filters": ["info_filter"],
            },
            "log_dat_handler": {
                "()": "ttex.log.coco.ManualRotatingFileHandler",
                "filepath": "coco_log_dat.txt",
                "key": "log_dat",
                "mode": "a",
                "formatter": "log_dat_form",
                "filters": ["log_dat_filter"],
            },
            "log_tdat_handler": {
                "()": "ttex.log.coco.ManualRotatingFileHandler",
                "filepath": "coco_log_tdat.txt",
                "key": "log_tdat",
                "mode": "a",
                "formatter": "log_tdat_form",
                "filters": ["log_tdat_filter"],
            },
        },
        "loggers": {
            logger_name: {
                "level": "INFO",
                "filters": ["coco_filter"],
                "handlers": ["info_handler", "log_dat_handler", "log_tdat_handler"],
            }
        },
    }
    return config_dict


# TODO: activate and test
