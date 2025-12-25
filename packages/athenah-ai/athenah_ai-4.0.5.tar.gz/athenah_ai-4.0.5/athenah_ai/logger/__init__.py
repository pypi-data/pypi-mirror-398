import logging

# Create a logger
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)  # Set the logging level (use DEBUG to see document previews)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Set the logging level for the handler (use DEBUG to see document previews)

# Create a formatter and set it for the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)
