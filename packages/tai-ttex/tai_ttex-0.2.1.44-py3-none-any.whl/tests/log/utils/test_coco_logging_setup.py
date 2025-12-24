from ttex.log.utils.coco_logging_setup import setup_coco_logger, teardown_coco_logger


def test_setup_teardown_coco_logger():
    setup_params = {
        "name": "test_coco_logger",
        "base_evaluation_triggers": [1, 2, 5],
        "number_evaluation_triggers": 20,
        "improvement_steps": 1e-5,
        "number_target_triggers": 20,
        "target_precision": 1e-8,
    }

    logger = setup_coco_logger(**setup_params)
    assert logger is not None
    assert logger.name == "test_coco_logger"
    assert len(logger.handlers) == 3  # info, log_dat, log_tdat handlers

    # Check that handlers are instances of ManualRotatingFileHandler
    for handler in logger.handlers:
        from ttex.log.handler import ManualRotatingFileHandler

        assert isinstance(handler, ManualRotatingFileHandler)
    logger.info("This is a test log message.")
    assert logger._coco_setup is True  # Ensure setup flag is set
    assert len(logger.filters) == 1  # One filter added in setup
    logger.addFilter(lambda record: True)  # Add a dummy filter
    assert len(logger.filters) == 2  # One from setup and one we just added

    logger = setup_coco_logger(**setup_params)  # Call setup again
    assert len(logger.handlers) == 3  # Handlers should not be duplicated
    assert len(logger.filters) == 2  # Filters should not be duplicated
    assert logger._coco_setup is True  # Setup flag should remain True
    logger.info("This is another test log message.")

    # Teardown the logger
    teardown_coco_logger(name="test_coco_logger")
    # After teardown, handlers should be closed and removed
    assert len(logger.handlers) == 0
    assert len(logger.filters) == 0  # All filters should be removed
    assert logger._coco_setup is False  # Setup flag should be Reset

    # Teardown again to ensure no errors occur
    teardown_coco_logger(name="test_coco_logger")
    assert len(logger.handlers) == 0  # Still no handlers
    assert len(logger.filters) == 0  # Still no filters
    assert logger._coco_setup is False  # Setup flag should remain Reset

    # Setup again to ensure it can be re-initialized
    logger = setup_coco_logger(**setup_params)
    assert len(logger.handlers) == 3  # Handlers should be re-initialized
    assert len(logger.filters) == 1  # Filters should be re-initialized
    assert logger._coco_setup is True  # Setup flag should be set again
    logger.info("This is a test log message after re-setup.")
