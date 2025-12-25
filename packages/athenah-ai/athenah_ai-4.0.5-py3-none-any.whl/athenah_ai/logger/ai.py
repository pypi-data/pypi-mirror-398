import json
import logging

# Create a logger
ai_logger = logging.getLogger("ai")
ai_logger.setLevel(logging.INFO)  # Set the logging level

# Create a console handler
file_handler = logging.FileHandler("ai.log")
file_handler.setLevel(logging.INFO)  # Set the logging level for the handler

# Create a formatter and set it for the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(prompt)s")
file_handler.setFormatter(formatter)

# Add the handler to the logger
ai_logger.addHandler(file_handler)


def log_ai(role: str = "system", content: str = ""):
    ai_content = {"role": role, "content": content}
    ai_logger.info("AI LOG", extra={"prompt": json.dumps(ai_content)})
