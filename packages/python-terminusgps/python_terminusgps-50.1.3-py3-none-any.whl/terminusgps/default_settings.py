import os
import pathlib

from terminusgps.authorizenet.constants import Environment, ValidationMode

BASE_DIR = pathlib.Path(__file__).resolve().parent

DEBUG = True
SECRET_KEY = "xem*6no%8d9%^qzt2f3x3ar-uq4_+7h9myc$t0!+4%bj5us6f)"
USE_TZ = False
USE_I18N = False

MERCHANT_AUTH_ENVIRONMENT = Environment.SANDBOX
MERCHANT_AUTH_VALIDATION_MODE = ValidationMode.TEST

# Secrets
MERCHANT_AUTH_LOGIN_ID = os.getenv("MERCHANT_AUTH_LOGIN_ID")
MERCHANT_AUTH_TRANSACTION_KEY = os.getenv("MERCHANT_AUTH_TRANSACTION_KEY")
WIALON_TOKEN = os.getenv("WIALON_TOKEN")
