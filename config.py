"""Application configuration loaded from environment variables."""

import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_NAME = os.getenv('APP_NAME', 'AutoSure')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'car_service_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

    @property
    def DATABASE_URL(self):
        env_url = os.getenv('DATABASE_URL')
        if env_url:
            return env_url
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    COMPANY_NAME = os.getenv('COMPANY_NAME', 'Easy Ride Auto Service')
    COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', 'Gujarat, India')
    COMPANY_PHONE = os.getenv('COMPANY_PHONE', '+91 98765 43210')
    COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', 'info@easyride.com')

    TAX_RATE = Decimal(os.getenv('TAX_RATE', '0.18'))
    TAX_NAME = os.getenv('TAX_NAME', 'GST')

    INVOICE_PREFIX = os.getenv('INVOICE_PREFIX', 'INV')
    ORDER_PREFIX = os.getenv('ORDER_PREFIX', 'WO')
    PAYMENT_TERMS_DAYS = int(os.getenv('PAYMENT_TERMS_DAYS', '30'))

    CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '₹')
    CURRENCY_CODE = os.getenv('CURRENCY_CODE', 'INR')

    DEFAULT_LABOR_RATE = Decimal(os.getenv('DEFAULT_LABOR_RATE', '500.00'))
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))
    LOW_STOCK_THRESHOLD = int(os.getenv('LOW_STOCK_THRESHOLD', '10'))

    INVENTORY_CATEGORIES = [
        'Electrical', 'Exterior', 'Filters', 'Brakes', 'Ignition', 'Fluids'
    ]

    CATEGORY_CODE_MAP = {
        'Electrical': 'ELC',
        'Exterior': 'EXT',
        'Filters': 'FLT',
        'Brakes': 'BRK',
        'Ignition': 'IGN',
        'Fluids': 'OIL',
    }


app_config = Config()
