"""
Configuration utilities for environment variables and settings.
"""
from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    EMAIL_SENDER = getenv("EMAIL_SENDER")
    EMAIL_SENDER_ADDRESS = getenv("EMAIL_SENDER_ADDRESS")
    EMAIL_RECIPIENT_0_NAME = getenv("EMAIL_RECIPIENT_0_NAME")
    EMAIL_RECIPIENT_0_ADDRESS = getenv("EMAIL_RECIPIENT_0_ADDRESS")
    PROD_MODE = getenv("PROD_MODE", "false").lower() == "true"
