import os
import json
import time
import random
import asyncio
import threading
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, error
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
import customtkinter as ctk
import tkinter.messagebox
import logging
import sys
import re
import configparser

try:
    import undetected_chromedriver as uc
    UNDETECTED_CHROME_AVAILABLE = True
    logging.info("✅ Undetected-chromedriver available")
except ImportError:
    UNDETECTED_CHROME_AVAILABLE = False
    logging.info("ℹ️ Using standard Chrome mode")

# --- Configuration ---
CONFIG_FILE = 'config.txt'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        logging.critical(f"{CONFIG_FILE} not found!")
        raise FileNotFoundError(f"{CONFIG_FILE} not found!")
        
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding='utf-8')
    return config['Settings']

try:
    config = load_config()
    SMS_AMOUNT = float(config.get('SMS_AMOUNT', 0.0078))
    WITHDRAWAL_LIMIT = float(config.get('WITHDRAWAL_LIMIT', 50))
    BINANCE_MINIMUM_WITHDRAWAL = float(config.get('BINANCE_MINIMUM_WITHDRAWAL', 1250))
    REFERRAL_WITHDRAWAL_BONUS_PERCENT = float(config.get('REFERRAL_WITHDRAWAL_BONUS_PERCENT', 5))
    PAYMENT_METHODS = [method.strip() for method in config.get('PAYMENT_METHOD', 'Bkash,Nagad,Binance').split(',')]
except (FileNotFoundError, KeyError, ValueError) as e:
    print(f"Configuration Error: {e}")
    SMS_AMOUNT, WITHDRAWAL_LIMIT, REFERRAL_WITHDRAWAL_BONUS_PERCENT = 0.0078, 50.0, 5.0
    BINANCE_MINIMUM_WITHDRAWAL = 1250.0
    PAYMENT_METHODS = ["Bkash", "Nagad", "Binance"]
    
TELEGRAM_BOT_TOKEN = "8474091696:AAHZdQJ3T83zGqfcMyl4yJK1sLWaCFRkGaw"
GROUP_ID = -1003042851684
PAYMENT_CHANNEL_ID = -1003054116681
ADMIN_ID = 6080330271 
GROUP_LINK = "https://t.me/+ICxGsNEW2W9kMDg1"
EMAIL = "shahidul7616@gmail.com"
PASSWORD = "SRshAhidul@2025"
ADMIN_USERNAME = "shahidul761" 

# File Paths
USERS_FILE = 'users.json'
SMS_CACHE_FILE = 'sms.txt'
SENT_SMS_FILE = 'sent_sms.json'
NUMBERS_FILE = 'numbers.txt' 
NUMBER_USAGE_FILE = 'number_usage.json'

COUNTRY_CODES = {
    '+1': 'US', '+44': 'UK', '+33': 'FR', '+49': 'DE', '+39': 'IT', '+34': 'ES', 
    '+86': 'CN', '+81': 'JP', '+82': 'KR', '+91': 'IN', '+61': 'AU', '+55': 'BR',
    '+7': 'RU', '+92': 'PK', '+94': 'LK', '+95': 'MM',
    # New countries
    '+228': 'TOGO', '+225': 'IVORY_COAST', '+62': 'INDONESIA', '+63': 'PHILIPPINES', 
    '+261': 'MADAGASCAR', '+20': 'EGYPT', '+234': 'NIGERIA', '+852': 'HONG_KONG', '+375': 'BELARUS',
    '+93': 'AFGHANISTAN', '+51': 'PERU', '+593': 'ECUADOR', '+591': 'BOLIVIA', '+1876': 'JAMAICA',
    '+224': 'GUINEA', '+977': 'NEPAL'
}

COUNTRY_FLAGS = {
    'US': '🇺🇸 United States',
    'UK': '🇬🇧 United Kingdom', 
    'FR': '🇫🇷 France',
    'DE': '🇩🇪 Germany',
    'IT': '🇮🇹 Italy',
    'ES': '🇪🇸 Spain',
    'CN': '🇨🇳 China',
    'JP': '🇯🇵 Japan',
    'KR': '🇰🇷 South Korea',
    'IN': '🇮🇳 India',
    'AU': '🇦🇺 Australia',
    'BR': '🇧🇷 Brazil',
    'RU': '🇷🇺 Russia',
    'PK': '🇵🇰 Pakistan',
    'LK': '🇱🇰 Sri Lanka',
    'MM': '🇲🇲 Myanmar',
    'TOGO': '🇹🇬 Togo',
    'IVORY_COAST': '🇨🇮 Côte d\'Ivoire',
    'INDONESIA': '🇮🇩 Indonesia',
    'PHILIPPINES': '🇵🇭 Philippines',
    'MADAGASCAR': '🇲🇬 Madagascar',
    'EGYPT': '🇪🇬 Egypt',
    'NIGERIA': '🇳🇬 Nigeria',
    'HONG_KONG': '🇭🇰 Hong Kong',
    'BELARUS': '🇧🇾 Belarus',
    'AFGHANISTAN': '🇦🇫 Afghanistan',
    'PERU': '🇵🇪 Peru',
    'ECUADOR': '🇪🇨 Ecuador',
    'BOLIVIA': '🇧🇴 Bolivia',
    'JAMAICA': '🇯🇲 Jamaica',
    'GUINEA': '🇬🇳 Guinea',
    'NEPAL': '🇳🇵 Nepal',
    'Unknown': '❓ Unknown'
}

def detect_country_from_number(phone_number):
    """Fast country detection using optimized lookup."""
    if not phone_number:
        return 'Unknown'
    
    phone_str = str(phone_number).strip()
    clean_number = phone_str.replace('+', '').replace('-', '').replace(' ', '').lstrip('0')
    
    # Check exact matches first
    for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):
        if phone_str.startswith(code) or clean_number.startswith(code.replace('+', '')):
            return COUNTRY_CODES[code]
    
    # Quick common country checks
    if clean_number.startswith('1'): return 'US'
    elif clean_number.startswith('44'): return 'UK'
    elif clean_number.startswith('92'): return 'PK'
    elif clean_number.startswith('91'): return 'IN'
    elif clean_number.startswith('86'): return 'CN'
    elif clean_number.startswith('81'): return 'JP'
    elif clean_number.startswith('82'): return 'KR'
    elif clean_number.startswith('62'): return 'INDONESIA'
    elif clean_number.startswith('63'): return 'PHILIPPINES'
    elif clean_number.startswith('261'): return 'MADAGASCAR'
    elif clean_number.startswith('20'): return 'EGYPT'
    elif clean_number.startswith('234'): return 'NIGERIA'
    elif clean_number.startswith('852'): return 'HONG_KONG'
    elif clean_number.startswith('375'): return 'BELARUS'
    elif clean_number.startswith('228'): return 'TOGO'
    elif clean_number.startswith('225'): return 'IVORY_COAST'
    elif clean_number.startswith('93'): return 'AFGHANISTAN'
    elif clean_number.startswith('51'): return 'PERU'
    elif clean_number.startswith('593'): return 'ECUADOR'
    elif clean_number.startswith('591'): return 'BOLIVIA'
    elif clean_number.startswith('1876'): return 'JAMAICA'
    elif clean_number.startswith('224'): return 'GUINEA'
    elif clean_number.startswith('977'): return 'NEPAL'
    elif clean_number.startswith('7'): return 'RU'
    elif clean_number.startswith('49'): return 'DE'
    elif clean_number.startswith('33'): return 'FR'
    
    return 'Unknown'

shutdown_event = asyncio.Event()
bot_thread = None
manager_instance = None
json_lock = threading.Lock()

class SmartCache:
    """Intelligent caching system for better performance."""
    
    def __init__(self):
        self._user_cache = {}
        self._country_cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 300  # 5 minutes
    
    def get_user_data(self, user_id: str):
        """Get user data with smart caching."""
        current_time = time.time()
        
        if (user_id in self._user_cache and 
            current_time - self._cache_timestamps.get(user_id, 0) < self._cache_ttl):
            return self._user_cache[user_id]
        
        # Load from file and cache
        users_data = load_json_data(USERS_FILE, {})
        user_data = users_data.get(user_id, {})
        
        self._user_cache[user_id] = user_data
        self._cache_timestamps[user_id] = current_time
        
        return user_data
    
    def update_user_data(self, user_id: str, user_data: dict):
        """Update user data and cache."""
        self._user_cache[user_id] = user_data
        self._cache_timestamps[user_id] = time.time()
        
        # Also update file
        users_data = load_json_data(USERS_FILE, {})
        users_data[user_id] = user_data
        save_json_data(USERS_FILE, users_data)
    
    def get_countries(self):
        """Get countries with caching."""
        current_time = time.time()
        
        if (current_time - self._cache_timestamps.get('countries', 0) < self._cache_ttl):
            return self._country_cache
        
        # Refresh cache
        countries = manager_instance.get_available_countries()
        self._country_cache = countries
        self._cache_timestamps['countries'] = current_time
        
        return countries
    
    def clear_cache(self):
        """Clear all caches."""
        self._user_cache.clear()
        self._country_cache.clear()
        self._cache_timestamps.clear()

smart_cache = SmartCache()

logging.basicConfig(filename='bot_error.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

class UserManager:
    
    @staticmethod
    def get_user_stats():
        users_data = load_json_data(USERS_FILE, {})
        
        total_users = len(users_data)
        active_users = sum(1 for user in users_data.values() if user.get('phone_numbers'))
        users_with_balance = sum(1 for user in users_data.values() if user.get('balance', 0) > 0)
        total_balance = sum(user.get('balance', 0) for user in users_data.values())
        total_referrals = sum(user.get('referrals', 0) for user in users_data.values())
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'users_with_balance': users_with_balance,
            'total_balance': total_balance,
            'total_referrals': total_referrals,
            'average_balance': total_balance / total_users if total_users > 0 else 0
        }
    
    @staticmethod
    def update_user_balance(user_id: str, amount: float, reason: str = "SMS"):
        users_data = load_json_data(USERS_FILE, {})
        
        if user_id not in users_data:
            return False
        
        user_data = users_data[user_id]
        old_balance = user_data.get('balance', 0)
        new_balance = old_balance + amount
        
        user_data['balance'] = new_balance
        
        if 'transactions' not in user_data:
            user_data['transactions'] = []
        
        user_data['transactions'].append({
            'timestamp': datetime.now().isoformat(),
            'type': 'credit',
            'amount': amount,
            'reason': reason,
            'old_balance': old_balance,
            'new_balance': new_balance
        })
        
        # Keep only last 50 transactions
        user_data['transactions'] = user_data['transactions'][-50:]
        
        users_data[user_id] = user_data
        save_json_data(USERS_FILE, users_data)
        
        logging.info(f"Updated balance for user {user_id}: {old_balance:.4f} -> {new_balance:.4f} ({reason})")
        return True
    
    @staticmethod
    def deduct_user_balance(user_id: str, amount: float, reason: str = "Withdrawal"):
        """Deduct user balance with transaction logging."""
        users_data = load_json_data(USERS_FILE, {})
        
        if user_id not in users_data:
            return False
        
        user_data = users_data[user_id]
        old_balance = user_data.get('balance', 0)
        
        if old_balance < amount:
            return False
        
        new_balance = old_balance - amount
        user_data['balance'] = new_balance
        
        # Add transaction log
        if 'transactions' not in user_data:
            user_data['transactions'] = []
        
        user_data['transactions'].append({
            'timestamp': datetime.now().isoformat(),
            'type': 'debit',
            'amount': amount,
            'reason': reason,
            'old_balance': old_balance,
            'new_balance': new_balance
        })
        
        # Keep only last 50 transactions
        user_data['transactions'] = user_data['transactions'][-50:]
        
        users_data[user_id] = user_data
        save_json_data(USERS_FILE, users_data)
        
        logging.info(f"Deducted balance for user {user_id}: {old_balance:.4f} -> {new_balance:.4f} ({reason})")
        return True

def load_json_data(filepath, default_data):
    with json_lock:
        if not os.path.exists(filepath):
            return default_data
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default_data

def save_json_data(filepath, data):
    with json_lock:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def load_sent_sms_keys():
    return set(load_json_data(SENT_SMS_FILE, []))

def save_sent_sms_keys(keys):
    save_json_data(SENT_SMS_FILE, list(keys))

def load_number_usage():
    """Load number usage tracking data."""
    return load_json_data(NUMBER_USAGE_FILE, {})

def save_number_usage(usage_data):
    """Save number usage tracking data."""
    save_json_data(NUMBER_USAGE_FILE, usage_data)

def increment_number_usage(number):
    """Increment usage count for a number and return current count."""
    usage_data = load_number_usage()
    current_count = usage_data.get(number, 0) + 1
    usage_data[number] = current_count
    save_number_usage(usage_data)
    return current_count

def get_number_usage_count(number):
    """Get current usage count for a number."""
    usage_data = load_number_usage()
    return usage_data.get(number, 0)

def extract_otp_from_text(text):
    if not text: return "N/A"
    patterns = [r'G-(\d{6})', r'code is\s*(\d+)', r'code:\s*(\d+)', r'verification code[:\s]*(\d+)', r'OTP is\s*(\d+)', r'pin[:\s]*(\d+)', r'(\d{6})', r'(\d{4,8})']
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            otp = match.group(1)
            if 4 <= len(otp) <= 8 and otp.isdigit():
                return otp
    fallback_match = re.search(r'\b(\d{4,8})\b', text)
    return fallback_match.group(1) if fallback_match else "N/A"

def html_escape(text):
    return str(text).replace('<', '&lt;').replace('>', '&gt;')

def hide_number(number):
    if len(str(number)) > 7:
        num_str = str(number)
        return f"{num_str[:3]}XXXX{num_str[-4:]}"
    return number

def format_phone_number(number):
    """Format phone number to show both with and without country code."""
    if not number:
        return "N/A"
    
    number_str = str(number).strip()
    
    # If number starts with +, it has country code
    if number_str.startswith('+'):
        # Remove + for local format
        local_format = number_str[1:]
        return f"<b>with country code:</b>\n<code>{number_str}</code>\n<b>without country code:</b>\n<code>{local_format}</code>"
    else:
        # Check if number already starts with a country code (without +)
        detected_country = detect_country_from_number(number_str)
        if detected_country != 'Unknown':
            # Find the country code for this country
            country_code = None
            for code, country in COUNTRY_CODES.items():
                if country == detected_country:
                    country_code = code.replace('+', '')  # Remove + for comparison
                    break
            
            if country_code and number_str.startswith(country_code):
                # Number already has country code, just add + for international format
                international_format = f"+{number_str}"
                local_format = number_str[len(country_code):]  # Remove country code for local format
                return f"<b>with country code:</b>\n<code>{international_format}</code>\n<b>without country code:</b>\n<code>{local_format}</code>"
            elif country_code:
                # Number doesn't have country code, add it
                international_format = f"+{country_code}{number_str}"
                return f"<b>with country code:</b>\n<code>{international_format}</code>\n<b>without country code:</b>\n<code>{number_str}</code>"
        
        # If we can't determine country code, just show the number
        return f"<code>{number_str}</code>"

# --- IvaSmsManager Class (Web Scraping) ---
class IvaSmsManager:
    _instance = None
    _sms_driver = None
    _is_initialized = False
    _numbers_scraped = False  # Flag to track if numbers have been scraped
    _lock = threading.Lock() # Lock for file operations
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(IvaSmsManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._is_initialized:
            self._initialize_drivers()
            self._last_refresh_time = time.time()
    
    def _create_driver(self):
        """Create optimized Chrome driver."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                import uuid
                session_id = str(uuid.uuid4())[:8]
                user_data_dir = os.path.join(os.getcwd(), f"chrome_user_data_{session_id}")
                if not os.path.exists(user_data_dir):
                    os.makedirs(user_data_dir)
                
                driver = None
                
                # Try undetected-chromedriver first
                if UNDETECTED_CHROME_AVAILABLE:
                    try:
                        driver = uc.Chrome(
                            user_data_dir=user_data_dir,
                            headless=False,
                            use_subprocess=False,
                            suppress_welcome=True,
                            no_sandbox=True
                        )
                        logging.info("✅ Created undetected Chrome driver")
                    except Exception as uc_error:
                        logging.warning(f"Undetected-chromedriver failed: {uc_error}")
                        driver = None
                
                # Fallback to standard Chrome
                if driver is None:
                    chrome_paths = [
                        "chromedriver.exe",
                        os.path.join(os.getcwd(), "chromedriver.exe"),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver.exe")
                    ]
                    
                    chromedriver_path = None
                    for path in chrome_paths:
                        if os.path.exists(path):
                            chromedriver_path = path
                            break
                    
                    if not chromedriver_path:
                        raise FileNotFoundError(f"chromedriver.exe not found. Checked: {chrome_paths}")
                    
                    service = Service(chromedriver_path)
                    options = webdriver.ChromeOptions()
                    
                    # Optimized Chrome options
                    options.add_argument(f'--user-data-dir={user_data_dir}')
                    options.add_argument('--profile-directory=Default')
                    options.add_argument("--window-size=1920,1080")
                    options.add_argument("--start-maximized")
                    options.add_argument("--log-level=3")
                    options.add_argument("--disable-headless-mode")
                    options.add_argument("--no-first-run")
                    options.add_argument("--disable-default-browser-check")
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.55 Safari/537.36')
                    
                    try:
                        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
                        options.add_experimental_option('useAutomationExtension', False)
                    except Exception:
                        pass
                    
                    driver = webdriver.Chrome(service=service, options=options)
                
                # Apply essential stealth scripts
                stealth_scripts = [
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
                    "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
                    "window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} }",
                    "Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'})",
                    "Object.defineProperty(navigator, 'platform', {get: () => 'Win32'})"
                ]
                
                for script in stealth_scripts:
                    try:
                        driver.execute_script(script)
                    except Exception:
                        pass
                
                logging.info("✅ Created optimized browser instance")
                return driver
            except Exception as e:
                logging.error(f"Driver creation attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(3)
                else:
                    raise
    
    def _initialize_drivers(self):
        # Initialize SMS driver and scrape numbers once
        self._sms_driver = self._create_driver()
        self._is_initialized = True
        self._setup_driver(self._sms_driver, "https://www.ivasms.com/portal/live/my_sms")
        
        # Scrape numbers once at startup
        if not self._numbers_scraped:
            self._scrape_numbers_once()
            self._numbers_scraped = True


    def _login_driver(self, driver):
        """Login to ivasms.com."""
        try:
            logging.info("🔐 Logging in to ivasms.com...")
            driver.get("https://www.ivasms.com/login")
            time.sleep(3)
            
            wait = WebDriverWait(driver, 20)
            
            email_field = wait.until(EC.visibility_of_element_located((By.NAME, "email")))
            email_field.clear()
            email_field.send_keys(EMAIL)
            time.sleep(1)
            
            password_field = driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            time.sleep(1)
            
            login_button = driver.find_element(By.TAG_NAME, "button")
            login_button.click()
            
            wait.until(EC.url_contains("portal"))
            time.sleep(2)
            
            logging.info("✅ Login completed")
            
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            raise

    def _click_tutorial_popups(self, driver):
        """Click tutorial popups if they appear."""
        for _ in range(5):
            try:
                wait = WebDriverWait(driver, 3)
                next_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.driver-popover-next-btn"))
                )
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(0.5)
            except Exception:
                break

    def _setup_driver(self, driver, url):
        try:
            self._login_driver(driver)
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self._click_tutorial_popups(driver)
        except Exception as e:
            logging.error(f"Failed to setup driver for {url}: {e}")
            raise

    def refresh_sms_page(self):
        """Refresh SMS page every 20 minutes."""
        try:
            current_time = time.time()
            time_since_refresh = current_time - self._last_refresh_time
            
            if time_since_refresh >= 1200:
                logging.info(f"🔄 Refreshing SMS page after {time_since_refresh/60:.1f} minutes")
                
                self._sms_driver.get("https://www.ivasms.com/portal/live/my_sms")
                WebDriverWait(self._sms_driver, 20).until(EC.presence_of_element_located((By.ID, "LiveTestSMS")))
                
                self._last_refresh_time = current_time
                logging.info("✅ SMS page refreshed")
            else:
                logging.debug(f"SMS page refresh not needed yet. Next refresh in {(1200 - time_since_refresh)/60:.1f} minutes")
                
        except Exception as e:
            logging.error(f"Failed to refresh SMS page: {e}")
            try:
                self._setup_driver(self._sms_driver, "https://www.ivasms.com/portal/live/my_sms")
                self._last_refresh_time = time.time()
                logging.info("✅ SMS driver setup after page refresh failure")
            except Exception as fallback_e:
                logging.error(f"Failed to setup SMS driver after page refresh failure: {fallback_e}")

    def scrape_and_save_all_sms(self):
        # Refresh SMS page if needed before scraping
        self.refresh_sms_page()
        
        try:
            WebDriverWait(self._sms_driver, 20).until(EC.presence_of_element_located((By.ID, "LiveTestSMS")))
            soup = BeautifulSoup(self._sms_driver.page_source, "html.parser")
            table_body = soup.select_one("tbody#LiveTestSMS")
            if not table_body:
                return
            
            sms_list = []
            for row in table_body.select("tr"):
                try:
                    phone_elem = row.select_one("p.CopyText.text-500")
                    country_raw_elem = row.select_one("h6.mb-1.fw-semi-bold a")
                    provider_elem = row.select_one("div.fw-semi-bold.ms-2")
                    message_elem = row.select("td.align-middle.text-end.fw-semi-bold")

                    if phone_elem and country_raw_elem and provider_elem and message_elem:
                        phone = phone_elem.get_text(strip=True)
                        country_raw = country_raw_elem.get_text(strip=True)
                        country = re.sub(r'\d', '', country_raw).strip()
                        provider = provider_elem.get_text(strip=True)
                        message = message_elem[-1].get_text(strip=True)
                        sms_list.append({'country': country, 'provider': provider, 'message': message, 'phone': phone})
                except Exception as e:
                    logging.warning(f"Could not parse an SMS row: {e}")

            with open(SMS_CACHE_FILE, 'w', encoding='utf-8') as f:
                for sms in sms_list:
                    f.write(json.dumps(sms) + "\n")
        except Exception as e:
            logging.error(f"SMS scraping failed: {e}")
            self._setup_driver(self._sms_driver, "https://www.ivasms.com/portal/live/my_sms")

    def _scrape_numbers_once(self):
        """Scrapes all numbers once at startup and closes the driver permanently."""
        temp_driver = None
        try:
            logging.info("Starting one-time number scraping at startup...")
            temp_driver = self._create_driver()
            self._setup_driver(temp_driver, "https://www.ivasms.com/portal/numbers")
            
            wait = WebDriverWait(temp_driver, 20)
            select_elem = wait.until(EC.presence_of_element_located((By.NAME, "MyNumber_length")))
            Select(select_elem).select_by_value("1000")  # Load 1000 numbers
            time.sleep(10)  # Wait longer for 1000 numbers to load
            
            soup = BeautifulSoup(temp_driver.page_source, 'html.parser')
            number_elements = soup.select("#MyNumber tbody tr td.sorting_1")
            scraped_numbers = [elem.get_text(strip=True) for elem in number_elements]

            if not scraped_numbers:
                logging.warning("No numbers found on the page.")
                return

            # Detect countries for logging purposes
            detected_countries = set()
            for number in scraped_numbers:
                country = detect_country_from_number(number)
                logging.info(f"Detected country '{country}' for number '{number}'")
                detected_countries.add(country)
            
            logging.info(f"Total countries detected: {len(detected_countries)} - {list(detected_countries)}")
            
            # Debug: Show some example numbers and their detected countries
            sample_numbers = scraped_numbers[:5] if scraped_numbers else []
            for sample_num in sample_numbers:
                detected_c = detect_country_from_number(sample_num)
                logging.info(f"Sample: '{sample_num}' -> '{detected_c}'")

            with self._lock:
                if os.path.exists(NUMBERS_FILE):
                    with open(NUMBERS_FILE, 'r', encoding='utf-8') as f:
                        existing_numbers = {line.strip() for line in f}
                else:
                    existing_numbers = set()

                users_data = load_json_data(USERS_FILE, {})
                assigned_numbers = set()
                for user in users_data.values():
                    assigned_numbers.update(user.get("phone_numbers", []))

                new_numbers = set(scraped_numbers) - existing_numbers - assigned_numbers
                
                if new_numbers:
                    with open(NUMBERS_FILE, 'a', encoding='utf-8') as f:
                        for num in new_numbers:
                            f.write(f"{num}\n")
                    logging.info(f"Added {len(new_numbers)} new numbers to {NUMBERS_FILE}.")
                else:
                    logging.info("No new numbers to add.")

        except Exception as e:
            logging.error(f"Failed to scrape numbers at startup: {e}")
        finally:
            # Always close the temporary driver permanently
            if temp_driver:
                try:
                    temp_driver.quit()
                    logging.info("Numbers driver closed permanently after one-time scraping.")
                except Exception as e:
                    logging.error(f"Error closing numbers driver: {e}")

    def scrape_and_save_all_numbers(self):
        """Disabled - numbers scraped once at startup."""
        return

    def get_available_countries(self):
        """Get available countries with counts."""
        countries = []
        country_counts = {}
        
        with self._lock:
            if not os.path.exists(NUMBERS_FILE):
                return countries
                
            with open(NUMBERS_FILE, 'r', encoding='utf-8') as f:
                users_data = load_json_data(USERS_FILE, {})
                assigned_numbers = set()
                for user in users_data.values():
                    assigned_numbers.update(user.get("phone_numbers", []))
                
                for line in f:
                    number = line.strip()
                    if number and number not in assigned_numbers:
                        country = detect_country_from_number(number)
                        country_counts[country] = country_counts.get(country, 0) + 1
        
        for country, count in country_counts.items():
            if count > 0:
                countries.append({'name': country, 'count': count})
        
        return sorted(countries, key=lambda x: x['count'], reverse=True)

    def assign_number_to_user(self, user_id: str, country: str = None) -> dict:
        """Smart number assignment with enhanced tracking and 3-time usage limit."""
        users_data = load_json_data(USERS_FILE, {})
        
        if user_id not in users_data:
            return {'success': False, 'error': 'User not found'}
        
        user_data = users_data[user_id]
        
        # Get number from file
        number = self.get_number_from_file(country)
        
        if not number:
            return {'success': False, 'error': 'No numbers available'}
        
        # Increment usage count for this number
        usage_count = increment_number_usage(number)
        
        # Update user data
        if 'phone_numbers' not in user_data:
            user_data['phone_numbers'] = []
        
        user_data['phone_numbers'].append(number)
        user_data['phone_numbers'] = user_data['phone_numbers'][-10:]  # Keep last 10
        user_data['last_number_time'] = time.time()
        
        # Add assignment log
        if 'number_assignments' not in user_data:
            user_data['number_assignments'] = []
        
        user_data['number_assignments'].append({
            'timestamp': datetime.now().isoformat(),
            'number': number,
            'country': country or 'Any',
            'total_assigned': len(user_data['phone_numbers']),
            'usage_count': usage_count
        })
        
        # Keep only last 20 assignments
        user_data['number_assignments'] = user_data['number_assignments'][-20:]
        
        users_data[user_id] = user_data
        save_json_data(USERS_FILE, users_data)
        
        logging.info(f"Assigned number {number} to user {user_id} (country: {country}, usage: {usage_count}/3)")
        
        return {
            'success': True,
            'number': number,
            'country': country or detect_country_from_number(number),
            'total_numbers': len(user_data['phone_numbers']),
            'usage_count': usage_count
        }
        
    def get_number_from_file(self, country=None):
        """Gets one number from numbers.txt for specified country using atomic file operations with cycling."""
        with self._lock:
            if not os.path.exists(NUMBERS_FILE):
                return None
            
            # Use temporary file for atomic operation
            temp_file = f"{NUMBERS_FILE}.tmp"
            number_to_give = None
            numbers_to_keep = []
            
            try:
                # Read all numbers from file
                with open(NUMBERS_FILE, 'r', encoding='utf-8') as original:
                    all_numbers = [line.strip() for line in original if line.strip()]
                
                if not all_numbers:
                    return None
                
                # Find the first available number for the country
                for number in all_numbers:
                    if country:
                        detected_country = detect_country_from_number(number)
                        if detected_country == country:
                            number_to_give = number
                            break
                    else:
                        number_to_give = number
                        break
                
                if not number_to_give:
                    return None
                
                # Check usage count and decide whether to keep or delete the number
                usage_count = get_number_usage_count(number_to_give)
                
                # Write all numbers except the one we're giving (if it's used 3 times, delete it)
                with open(temp_file, 'w', encoding='utf-8') as temp:
                    for number in all_numbers:
                        if number != number_to_give:
                            temp.write(f"{number}\n")
                        elif usage_count < 3:
                            # Keep the number if it hasn't been used 3 times yet
                            temp.write(f"{number}\n")
                        # If usage_count >= 3, don't write it (effectively deleting it)
                
                # Atomic replacement: temp file becomes the new numbers file
                os.replace(temp_file, NUMBERS_FILE)
                
                if usage_count >= 3:
                    logging.info(f"Number {number_to_give} deleted after {usage_count} uses")
                else:
                    logging.info(f"Assigned number {number_to_give} for country {country} (usage: {usage_count + 1}/3)")
                
                return number_to_give
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                logging.error(f"Error in get_number_from_file: {e}")
                return None

    def get_available_number_count(self):
        """Get count of available numbers."""
        with self._lock:
            if not os.path.exists(NUMBERS_FILE):
                return 0
            with open(NUMBERS_FILE, 'r', encoding='utf-8') as f:
                return len([line for line in f if line.strip()])
    
    def cleanup(self):
        """Clean up ChromeDriver instances."""
        logging.info("Cleaning up ChromeDriver instances.")
        try:
            if self._sms_driver:
                self._sms_driver.quit()
                logging.info("SMS driver quit successfully.")
        except Exception as e:
            logging.error(f"Error quitting SMS driver: {e}")
            
        self._sms_driver = None
        logging.info("ChromeDriver cleanup complete.")

# --- Telegram Bot UI and Logic ---

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("🎁 Get Number")],
        [KeyboardButton("👤 Account"), KeyboardButton("💰 Balance")],
        [KeyboardButton("💸 Withdraw"), KeyboardButton("📋 Withdraw History")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    users_data = load_json_data(USERS_FILE, {})

    if user_id not in users_data:
        referred_by = context.args[0] if context.args and context.args[0].isdigit() and context.args[0] != user_id else None
        
        users_data[user_id] = {
            "username": user.username, "first_name": user.first_name, "phone_numbers": [],
            "balance": 0, "referrals": 0, "referred_by": referred_by,
            "last_number_time": 0, "withdraw_history": []
        }
        
        if referred_by and referred_by in users_data:
            users_data[referred_by]['referrals'] = users_data[referred_by].get('referrals', 0) + 1
    
    save_json_data(USERS_FILE, users_data)
    
    welcome_text = (
        "<b>👋 Welcome!</b>\n\n"
        "<blockquote>Click any button below to get started:</blockquote>"
    )

    if update.callback_query:
        await update.callback_query.message.delete()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.HTML
        )

async def safe_answer_callback(query, text="", show_alert=False):
    """Safely answer callback query."""
    try:
        await query.answer(text=text, show_alert=show_alert)
        return True
    except (error.TimedOut, error.NetworkError) as e:
        logging.warning(f"Callback answer timeout: {e}")
        return False
    except error.BadRequest as e:
        logging.warning(f"Could not answer callback query: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error answering callback: {e}")
        return False

async def delete_message_after_delay(message, delay_seconds):
    """Delete message after delay."""
    try:
        await asyncio.sleep(delay_seconds)
        await message.delete()
    except Exception:
        pass

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer_callback(query)

    user_id = str(query.from_user.id)
    
    if query.data == 'main_menu':
        await start_command(update, context)
        return

    elif query.data.startswith('withdraw_method_'):
        method = query.data.split('_', 2)[2]
        
        min_withdraw = BINANCE_MINIMUM_WITHDRAWAL if method == 'Binance' else WITHDRAWAL_LIMIT
        
        users_data = load_json_data(USERS_FILE, {})
        balance = users_data.get(user_id, {}).get('balance', 0)

        if balance < min_withdraw:
            await query.answer(f"⚠️ Insufficient balance. You need at least ৳{min_withdraw:.2f} to withdraw via {method}.", show_alert=True)
            return

        context.user_data['withdrawal_method'] = method
        context.user_data['state'] = 'AWAITING_WITHDRAWAL_AMOUNT'
        
        cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_withdrawal')
        keyboard = InlineKeyboardMarkup([[cancel_button]])
        
        await query.edit_message_text(
            text=f"<b>💸 Withdrawing via {method}.</b>\n\n"
                 f"<blockquote>Please enter the amount you want to withdraw.\n"
                 f"The minimum for this method is ৳{min_withdraw:.2f}.</blockquote>\n\n"
                 f"<i>Click Cancel to abort the withdrawal process.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

    elif query.data.startswith('admin_accept_'):
        target_user_id = query.data.split('_')[2]
        await query.edit_message_text(f"<b>✅ Payment Approved. (User ID: {target_user_id})</b>", parse_mode=ParseMode.HTML)
        await context.bot.send_message(chat_id=target_user_id, text="<b>🎉 Congratulations! Your withdrawal request has been approved.</b>", parse_mode=ParseMode.HTML)

    elif query.data.startswith('admin_decline_'):
        target_user_id = query.data.split('_')[2]
        await query.edit_message_text(f"<b>❌ Payment Declined. (User ID: {target_user_id})</b>", parse_mode=ParseMode.HTML)
        await context.bot.send_message(chat_id=target_user_id, text="<b>😔 Sorry! Your withdrawal request has been declined.</b>", parse_mode=ParseMode.HTML)

    elif query.data == 'cancel_withdrawal':
        context.user_data['state'] = None
        context.user_data['withdrawal_method'] = None
        context.user_data['withdrawal_amount'] = None
        await query.edit_message_text(
            text="<b>❌ Withdrawal cancelled.</b>\n\n<blockquote>You can start a new withdrawal anytime.</blockquote>",
            parse_mode=ParseMode.HTML
        )

    elif query.data.startswith('country_'):
        country = query.data.split('_', 1)[1]
        await handle_country_selection(update, context, country)

    elif query.data == 'cancel_country_selection':
        context.user_data['state'] = None
        await query.edit_message_text(
            text="<b>❌ Country selection cancelled.</b>\n\n<blockquote>You can try again anytime.</blockquote>",
            parse_mode=ParseMode.HTML
        )
    

# --- Handlers for ReplyKeyboard buttons ---

async def handle_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, selected_country: str):
    """Enhanced country selection with better user experience."""
    user_id = str(update.effective_user.id)
    
    # Use the new assign_number_to_user method
    result = await asyncio.to_thread(manager_instance.assign_number_to_user, user_id, selected_country)
    
    if result['success']:
        # Reset state
        context.user_data['state'] = None
        
        country_display = COUNTRY_FLAGS.get(selected_country, f"🌍 {selected_country}")
        formatted_number = format_phone_number(result['number'])
        
        await update.callback_query.edit_message_text(
            text=f"<b>✅ Number Assigned Successfully!</b>\n\n"
                 f"<blockquote>🌍 <b>Country:</b> {country_display}\n"
                 f"📱 <b>Number:</b> {formatted_number}\n"
                 f"📊 <b>Total Numbers:</b> {result['total_numbers']}/10</blockquote>\n\n"
                 f"<b>📨 The OTP will be sent to our <a href='{GROUP_LINK}'>group</a> and your inbox.</b>\n\n"
                 f"<i>💡 You can get more numbers after 10 seconds cooldown.</i>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    else:
        country_display = COUNTRY_FLAGS.get(selected_country, f"🌍 {selected_country}")
        
        # Get available countries and show them
        available_countries = await asyncio.to_thread(manager_instance.get_available_countries)
        country_list = []
        for country in available_countries:
            country_name = country['name']
            country_flag = COUNTRY_FLAGS.get(country_name, f"🌍 {country_name}")
            country_list.append(f"{country_flag} ({country['count']})")
        
        error_msg = result.get('error', 'Unknown error')
        
        await update.callback_query.edit_message_text(
            text=f"<b>❌ Assignment Failed</b>\n\n"
                 f"<blockquote>🌍 <b>Requested:</b> {country_display}\n"
                 f"⚠️ <b>Error:</b> {error_msg}</blockquote>\n\n"
                 f"<b>📱 Available Countries:</b>\n"
                 f"<blockquote>{chr(10).join(country_list)}</blockquote>\n\n"
                 f"<i>Click 'Get Number' again to try another country.</i>",
            parse_mode=ParseMode.HTML
        )

async def handle_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced number getting with better user experience."""
    # Reset any withdrawal state when getting a number
    context.user_data['state'] = None
    context.user_data['withdrawal_method'] = None
    context.user_data['withdrawal_amount'] = None
    
    user_id = str(update.effective_user.id)
    users_data = load_json_data(USERS_FILE, {})
    user_data = users_data.get(user_id)
    
    if 'phone_numbers' not in user_data or not isinstance(user_data['phone_numbers'], list):
        user_data['phone_numbers'] = []

    cooldown = 10
    last_time = user_data.get('last_number_time', 0)
    current_time = time.time()

    if current_time - last_time < cooldown:
        remaining_time = int(cooldown - (current_time - last_time))
        await update.message.reply_text(
            f"<b>⏰ Please Wait</b>\n\n"
            f"<blockquote>🕐 <b>Cooldown:</b> {remaining_time} seconds remaining\n"
            f"📱 <b>Your Numbers:</b> {len(user_data['phone_numbers'])}/10\n"
            f"💰 <b>Your Balance:</b> ৳{user_data.get('balance', 0):.2f}</blockquote>",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Get available countries
    countries = await asyncio.to_thread(manager_instance.get_available_countries)
    
    if not countries:
        await update.message.reply_text(
            "<b>😔 No Numbers Available</b>\n\n"
            "<blockquote>📱 All numbers are currently assigned\n"
            f"💰 <b>Your Balance:</b> ৳{user_data.get('balance', 0):.2f}\n"
            f"📊 <b>Your Numbers:</b> {len(user_data['phone_numbers'])}/10</blockquote>\n\n"
            "<i>Please try again later or contact admin.</i>",
            parse_mode=ParseMode.HTML
        )
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"<b>⚠️ ADMIN ALERT: Bot out of numbers!</b>\n\n"
                     f"📊 <b>Total Users:</b> {len(users_data)}\n"
                     f"📱 <b>Active Users:</b> {sum(1 for u in users_data.values() if u.get('phone_numbers'))}\n"
                     f"💰 <b>Total Balance:</b> ৳{sum(u.get('balance', 0) for u in users_data.values()):.2f}",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logging.error(f"Failed to send out-of-stock notification to admin: {e}")
        return
    
    # Show country selection with enhanced UI
    context.user_data['state'] = 'SELECTING_COUNTRY'
    
    keyboard_buttons = []
    for country in countries:
        country_name = country['name']
        country_display = COUNTRY_FLAGS.get(country_name, f"🌍 {country_name}")
        button_text = f"{country_display} ({country['count']})"
        button = InlineKeyboardButton(button_text, callback_data=f"country_{country_name}")
        keyboard_buttons.append([button])
    
    cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_country_selection')
    keyboard_buttons.append([cancel_button])
    
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)
    
    await update.message.reply_text(
        f"<b>🌍 Choose Your Country</b>\n\n"
        f"<blockquote>📱 <b>Your Numbers:</b> {len(user_data['phone_numbers'])}/10\n"
        f"💰 <b>Your Balance:</b> ৳{user_data.get('balance', 0):.2f}\n"
        f"📊 <b>Available Countries:</b> {len(countries)}</blockquote>\n\n"
        f"<i>Select a country to get a number from that region.</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def handle_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users_data = load_json_data(USERS_FILE, {})
    user_data = users_data.get(user_id)
    
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    account_text = (
        f"<b>👤 Your Account</b>\n\n"
        f"<blockquote><b>Name:</b> {html_escape(user_data.get('first_name'))}\n"
        f"<b>Total Referrals:</b> {user_data.get('referrals', 0)}</blockquote>\n"
        f"<b>🔗 Your Referral Link:</b>\n<blockquote><code>{referral_link}</code></blockquote>\n"
        f"<b>Share this link. You will receive a {REFERRAL_WITHDRAWAL_BONUS_PERCENT}% bonus when your referred user withdraws.</b>"
    )
    await update.message.reply_text(account_text, parse_mode=ParseMode.HTML)

async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced balance display with detailed information."""
    user_id = str(update.effective_user.id)
    users_data = load_json_data(USERS_FILE, {})
    user_data = users_data.get(user_id, {})
    
    balance = user_data.get('balance', 0)
    phone_count = len(user_data.get('phone_numbers', []))
    referrals = user_data.get('referrals', 0)
    
    # Get recent transactions
    transactions = user_data.get('transactions', [])
    recent_transactions = transactions[-5:] if transactions else []
    
    balance_text = (
        f"<b>💰 Your Balance Overview</b>\n\n"
        f"<blockquote>💵 <b>Current Balance:</b> ৳{balance:.2f}\n"
        f"📱 <b>Phone Numbers:</b> {phone_count}/10\n"
        f"👥 <b>Referrals:</b> {referrals}\n"
        f"🎯 <b>Referral Bonus:</b> {REFERRAL_WITHDRAWAL_BONUS_PERCENT}%</blockquote>\n\n"
    )
    
    if recent_transactions:
        balance_text += f"<b>📊 Recent Activity:</b>\n"
        for tx in reversed(recent_transactions):
            timestamp = datetime.fromisoformat(tx['timestamp']).strftime("%m-%d %H:%M")
            tx_type = "➕" if tx['type'] == 'credit' else "➖"
            balance_text += f"<blockquote>{tx_type} ৳{tx['amount']:.4f} ({tx['reason']}) - {timestamp}</blockquote>"
    
    await update.message.reply_text(balance_text, parse_mode=ParseMode.HTML)

async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced withdrawal handler with better UX."""
    user_id = str(update.effective_user.id)
    users_data = load_json_data(USERS_FILE, {})
    user_data = users_data.get(user_id, {})
    
    balance = user_data.get('balance', 0)
    lowest_min_withdraw = min(WITHDRAWAL_LIMIT, BINANCE_MINIMUM_WITHDRAWAL)

    if balance < lowest_min_withdraw:
        await update.message.reply_text(
            f"<b>⚠️ Insufficient Balance</b>\n\n"
            f"<blockquote>💰 <b>Your Balance:</b> ৳{balance:.2f}\n"
            f"💸 <b>Minimum Required:</b> ৳{lowest_min_withdraw:.2f}\n\n"
            f"📱 <b>Earn more by:</b>\n"
            f"• Getting SMS numbers\n"
            f"• Referring friends\n"
            f"• Receiving OTP messages</blockquote>",
            parse_mode=ParseMode.HTML
        )
    else:
        # Enhanced withdrawal options with better formatting
        keyboard = []
        for method in PAYMENT_METHODS:
            min_amount = BINANCE_MINIMUM_WITHDRAWAL if method == 'Binance' else WITHDRAWAL_LIMIT
            button_text = f"💳 {method} (Min: ৳{min_amount:.0f})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'withdraw_method_{method}')])
        
        keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data='main_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"<b>💸 Withdrawal Options</b>\n\n"
            f"<blockquote>💰 <b>Your Total Balance:</b> ৳{balance:.2f}\n"
            f"📊 <b>Withdrawal Fee:</b> 2%\n"
            f"💡 <b>Example:</b> If you withdraw ৳100, you'll receive ৳98\n\n"
            f"💳 <b>Choose your preferred method:</b></blockquote>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def handle_withdrawal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced withdrawal amount handler with better validation."""
    if context.user_data.get('state') != 'AWAITING_WITHDRAWAL_AMOUNT':
        await handle_text_menu(update, context)
        return

    user_id = str(update.effective_user.id)
    users_data = load_json_data(USERS_FILE, {})
    user_data = users_data.get(user_id)
    balance = user_data.get('balance', 0)
    method = context.user_data.get('withdrawal_method', 'N/A')

    # Enhanced input validation
    input_text = update.message.text.strip()
    
    # Remove common currency symbols and spaces
    clean_input = input_text.replace('৳', '').replace('$', '').replace(',', '').replace(' ', '')
    
    if not clean_input.replace('.', '').isdigit():
        cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_withdrawal')
        keyboard = InlineKeyboardMarkup([[cancel_button]])
        await update.message.reply_text(
            "<b>⚠️ Invalid Amount</b>\n\n"
            "<blockquote>Please enter a valid number (e.g., 100, 100.50)\n"
            f"💡 <b>Your balance:</b> ৳{balance:.2f}</blockquote>\n\n"
            "<i>Click Cancel to abort the withdrawal process.</i>", 
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        return
    
    try:
        amount_to_withdraw = float(clean_input)
    except ValueError:
        cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_withdrawal')
        keyboard = InlineKeyboardMarkup([[cancel_button]])
        await update.message.reply_text(
            "<b>⚠️ Invalid Amount Format</b>\n\n"
            "<blockquote>Please enter a valid number\n"
            f"💡 <b>Your balance:</b> ৳{balance:.2f}</blockquote>\n\n"
            "<i>Click Cancel to abort the withdrawal process.</i>", 
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
        return
    
    min_withdraw = BINANCE_MINIMUM_WITHDRAWAL if method == 'Binance' else WITHDRAWAL_LIMIT

    if amount_to_withdraw < min_withdraw:
        cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_withdrawal')
        keyboard = InlineKeyboardMarkup([[cancel_button]])
        await update.message.reply_text(
            f"<b>⚠️ Minimum Amount Required</b>\n\n"
            f"<blockquote>💳 <b>Method:</b> {method}\n"
            f"💰 <b>Minimum:</b> ৳{min_withdraw:.2f}\n"
            f"📊 <b>Your Request:</b> ৳{amount_to_withdraw:.2f}</blockquote>\n\n"
            "<i>Click Cancel to abort the withdrawal process.</i>", 
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    elif amount_to_withdraw > balance:
        cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_withdrawal')
        keyboard = InlineKeyboardMarkup([[cancel_button]])
        await update.message.reply_text(
            f"<b>⚠️ Insufficient Balance</b>\n\n"
            f"<blockquote>💰 <b>Your Balance:</b> ৳{balance:.2f}\n"
            f"📊 <b>Requested Amount:</b> ৳{amount_to_withdraw:.2f}\n"
            f"📉 <b>Shortfall:</b> ৳{amount_to_withdraw - balance:.2f}</blockquote>\n\n"
            "<i>Click Cancel to abort the withdrawal process.</i>", 
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    else:
        context.user_data['withdrawal_amount'] = amount_to_withdraw
        context.user_data['state'] = 'AWAITING_WITHDRAWAL_INFO'
        
        info_prompt = f"Please enter your '{method}' number"
        if method == 'Binance':
            info_prompt = "Please enter your Binance Pay ID or Email"

        cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_withdrawal')
        keyboard = InlineKeyboardMarkup([[cancel_button]])
        
        # Calculate withdrawal fee (2%)
        withdrawal_fee = amount_to_withdraw * 0.02
        amount_received = amount_to_withdraw - withdrawal_fee
        
        await update.message.reply_text(
            f"<b>💸 Withdrawal Confirmation</b>\n\n"
            f"<blockquote>💰 <b>Your Total Balance:</b> ৳{balance:.2f}\n"
            f"💸 <b>Withdraw Amount:</b> ৳{amount_to_withdraw:.2f}\n"
            f"📊 <b>Withdrawal Fee (2%):</b> ৳{withdrawal_fee:.2f}\n"
            f"✅ <b>You Will Receive:</b> ৳{amount_received:.2f}\n"
            f"💳 <b>Method:</b> {method}\n"
            f"📉 <b>Remaining Balance:</b> ৳{balance - amount_to_withdraw:.2f}</blockquote>\n\n"
            f"<b>{info_prompt}:</b>\n\n"
            "<i>Click Cancel to abort the withdrawal process.</i>", 
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

async def handle_withdrawal_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') != 'AWAITING_WITHDRAWAL_INFO':
        await handle_text_menu(update, context)
        return

    user_id = str(update.effective_user.id)
    payment_info_input = update.message.text.strip()
    payment_method = context.user_data.get('withdrawal_method', 'N/A')
    amount_to_withdraw = context.user_data.get('withdrawal_amount')

    if not amount_to_withdraw:
        await update.message.reply_text("<b>⚠️ An error occurred. Please start the withdrawal process again.</b>", parse_mode=ParseMode.HTML)
        context.user_data['state'] = None
        return

    # Validate payment information based on method
    if payment_method != 'Binance':
        # For Bkash, Nagad, Rocket - only accept numeric values
        if not payment_info_input.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_withdrawal')
            keyboard = InlineKeyboardMarkup([[cancel_button]])
            await update.message.reply_text(
                f"<b>⚠️ Invalid {payment_method} number. Please enter numbers only (e.g., 01712345678).</b>\n\n<i>Click Cancel to abort the withdrawal process.</i>", 
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            return
    else:
        # For Binance - validate email format or numeric ID
        if '@' not in payment_info_input and not payment_info_input.isdigit():
            cancel_button = InlineKeyboardButton("❌ Cancel", callback_data='cancel_withdrawal')
            keyboard = InlineKeyboardMarkup([[cancel_button]])
            await update.message.reply_text(
                "<b>⚠️ Invalid Binance ID. Please enter your Binance Pay ID (email) or numeric ID.</b>\n\n<i>Click Cancel to abort the withdrawal process.</i>", 
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
            return

    payment_info = payment_info_input

    all_users_data = load_json_data(USERS_FILE, {})
    user_data = all_users_data[user_id]
    
    # Record withdrawal in history before deducting balance
    withdrawal_record = {
        "timestamp": datetime.now().isoformat(),
        "amount": amount_to_withdraw,
        "method": payment_method,
        "payment_info": payment_info,
        "status": "pending"
    }
    
    if 'withdraw_history' not in user_data:
        user_data['withdraw_history'] = []
    user_data['withdraw_history'].append(withdrawal_record)
    
    # Deduct balance
    user_data['balance'] -= amount_to_withdraw
    
    context.user_data['state'] = None
    context.user_data['withdrawal_method'] = None
    context.user_data['withdrawal_amount'] = None

    referrer_id = user_data.get("referred_by")
    if referrer_id:
        referrer_data = all_users_data.get(referrer_id)
        if referrer_data:
            bonus_amount = amount_to_withdraw * (REFERRAL_WITHDRAWAL_BONUS_PERCENT / 100.0)
            referrer_data['balance'] += bonus_amount
            
            try:
                await context.bot.send_message(
                    chat_id=int(referrer_id),
                    text=f"<b>🎉 Congratulations! A user you referred has withdrawn funds.</b>\n"
                         f"<blockquote>You have received a bonus of ৳{bonus_amount:.2f}."
                         f"</blockquote>",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logging.error(f"Could not send referral bonus notification to {referrer_id}: {e}")

    save_json_data(USERS_FILE, all_users_data)

    admin_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve", callback_data=f'admin_accept_{user_id}'),
         InlineKeyboardButton("❌ Decline", callback_data=f'admin_decline_{user_id}')]
    ])
    
    username = f"@{user_data.get('username')}" if user_data.get('username') else "N/A"
    
    # Calculate withdrawal fee (2%)
    withdrawal_fee = amount_to_withdraw * 0.02
    amount_received = amount_to_withdraw - withdrawal_fee
    
    admin_message = (
        f"<b>🔥 New Withdrawal Request!</b>\n\n"
        f"<b>👤 Admin:</b> @{ADMIN_USERNAME}\n"
        f"<b>📱 User:</b> {html_escape(user_data['first_name'])}\n"
        f"<b>🔗 Username:</b> {username}\n"
        f"<b>🆔 ID:</b> <code>{user_id}</code>\n\n"
        f"<b>💰 User's Total Balance:</b> ৳{user_data.get('balance', 0):.2f}\n"
        f"<b>💸 Withdraw Amount:</b> ৳{amount_to_withdraw:.2f}\n"
        f"<b>📊 Fee (2%):</b> ৳{withdrawal_fee:.2f}\n"
        f"<b>✅ Need to Pay User:</b> ৳{amount_received:.2f}\n"
        f"<b>💳 Method:</b> {payment_method}\n"
        f"<b>📞 Payment Info:</b> <code>{payment_info}</code>"
    )
    
    await context.bot.send_message(
        chat_id=PAYMENT_CHANNEL_ID, text=admin_message,
        parse_mode=ParseMode.HTML, reply_markup=admin_keyboard
    )
    
    await update.message.reply_text("<b>✅ Your withdrawal request has been submitted successfully. The admin will review it.</b>", parse_mode=ParseMode.HTML)

async def handle_withdraw_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users_data = load_json_data(USERS_FILE, {})
    user_data = users_data.get(user_id, {})
    
    withdraw_history = user_data.get('withdraw_history', [])
    
    if not withdraw_history:
        await update.message.reply_text("<b>📋 Withdraw History</b>\n\n<blockquote>No withdrawal history found.</blockquote>", parse_mode=ParseMode.HTML)
        return
    
    # Show last 10 withdrawals
    recent_withdrawals = withdraw_history[-10:]
    history_text = "<b>📋 Withdraw History (Last 10)</b>\n\n"
    
    for i, withdrawal in enumerate(reversed(recent_withdrawals), 1):
        timestamp = datetime.fromisoformat(withdrawal['timestamp']).strftime("%Y-%m-%d %H:%M")
        status_emoji = "✅" if withdrawal['status'] == "approved" else "⏳" if withdrawal['status'] == "pending" else "❌"
        history_text += f"<blockquote>{i}. {status_emoji} ৳{withdrawal['amount']:.2f} via {withdrawal['method']}\n"
        history_text += f"📅 {timestamp} - {withdrawal['status'].title()}</blockquote>\n"
    
    await update.message.reply_text(history_text, parse_mode=ParseMode.HTML)

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        logging.warning(f"Unauthorized broadcast attempt by {user.username}")
        return

    if not context.args:
        await update.message.reply_text("<b>Usage:</b> /update [your message]", parse_mode=ParseMode.HTML)
        return

    message_text = " ".join(context.args)
    formatted_message = f"<blockquote>{html_escape(message_text)}</blockquote>"
    
    users_data = load_json_data(USERS_FILE, {})
    user_ids = list(users_data.keys())
    
    success_count, fail_count = 0, 0
    
    await update.message.reply_text(f"📢 Starting to broadcast to {len(user_ids)} users...")

    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=formatted_message, parse_mode=ParseMode.HTML)
            success_count += 1
            await asyncio.sleep(0.1) # Avoid hitting rate limits
        except Exception as e:
            fail_count += 1
            logging.error(f"Failed to send broadcast to {user_id}: {e}")
            
    await update.message.reply_text(
        f"<b>📢 Broadcast Complete!</b>\n"
        f"✅ Sent successfully to {success_count} users.\n"
        f"❌ Failed to send to {fail_count} users.",
        parse_mode=ParseMode.HTML
    )

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced admin stats for monitoring 1k+ users."""
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        logging.warning(f"Unauthorized stats attempt by {user.username}")
        return

    stats = UserManager.get_user_stats()
    
    # Get additional metrics
    users_data = load_json_data(USERS_FILE, {})
    
    # Calculate more detailed stats
    balance_ranges = {
        '0-10': 0, '10-50': 0, '50-100': 0, '100+': 0
    }
    
    for user_data in users_data.values():
        balance = user_data.get('balance', 0)
        if balance < 10:
            balance_ranges['0-10'] += 1
        elif balance < 50:
            balance_ranges['10-50'] += 1
        elif balance < 100:
            balance_ranges['50-100'] += 1
        else:
            balance_ranges['100+'] += 1
    
    # Get top users by balance
    top_users = sorted(
        [(uid, data.get('balance', 0), data.get('first_name', 'Unknown')) 
         for uid, data in users_data.items()],
        key=lambda x: x[1], reverse=True
    )[:5]
    
    stats_message = (
        f"<b>📊 Bot Statistics (Enhanced)</b>\n\n"
        f"<blockquote>👥 <b>Total Users:</b> {stats['total_users']:,}\n"
        f"📱 <b>Active Users:</b> {stats['active_users']:,}\n"
        f"💰 <b>Users with Balance:</b> {stats['users_with_balance']:,}\n"
        f"💵 <b>Total Balance:</b> ৳{stats['total_balance']:,.2f}\n"
        f"📈 <b>Average Balance:</b> ৳{stats['average_balance']:.2f}\n"
        f"👥 <b>Total Referrals:</b> {stats['total_referrals']:,}</blockquote>\n\n"
        f"<b>💰 Balance Distribution:</b>\n"
        f"<blockquote>0-10: {balance_ranges['0-10']:,} users\n"
        f"10-50: {balance_ranges['10-50']:,} users\n"
        f"50-100: {balance_ranges['50-100']:,} users\n"
        f"100+: {balance_ranges['100+']:,} users</blockquote>\n\n"
        f"<b>🏆 Top Users by Balance:</b>\n"
    )
    
    for i, (uid, balance, name) in enumerate(top_users, 1):
        stats_message += f"<blockquote>{i}. {name}: ৳{balance:.2f}</blockquote>"
    
    await update.message.reply_text(stats_message, parse_mode=ParseMode.HTML)

async def sms_watcher_task(application: Application):
    """Optimized SMS watcher with smart caching for 1k+ users."""
    global manager_instance
    if not manager_instance:
        manager_instance = IvaSmsManager()
        
    while not shutdown_event.is_set():
        try:
            await asyncio.to_thread(manager_instance.scrape_and_save_all_sms)
            
            if not os.path.exists(SMS_CACHE_FILE):
                await asyncio.sleep(5)
                continue

            # Use smart cache for better performance
            users_data = load_json_data(USERS_FILE, {})
            sent_sms_keys = load_sent_sms_keys()
            new_sms_found_for_user = False
            
            # Build optimized phone-to-user mapping with caching
            phone_to_user_map = {}
            for uid, udata in users_data.items():
                for num in udata.get("phone_numbers", []):
                    normalized = str(num).replace('+', '').replace('-', '').replace(' ', '').strip()
                    phone_to_user_map[normalized] = uid
                    phone_to_user_map[str(num)] = uid

            with open(SMS_CACHE_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        sms_data = json.loads(line)
                        phone = sms_data.get('phone')
                        message = sms_data.get('message')

                        if not phone:
                            continue

                        unique_key = f"{phone}|{message}"
                        if unique_key in sent_sms_keys:
                            continue

                        otp = extract_otp_from_text(message)
                        
                        # Fast user detection with caching
                        normalized_phone = str(phone).replace('+', '').replace('-', '').replace(' ', '').strip()
                        owner_id = phone_to_user_map.get(normalized_phone) or phone_to_user_map.get(phone)
                        
                        # Simple fallback: try without leading zeros
                        if not owner_id:
                            clean_phone = normalized_phone.lstrip('0')
                            for stored_num, uid in phone_to_user_map.items():
                                stored_clean = str(stored_num).replace('+', '').replace('-', '').replace(' ', '').lstrip('0').strip()
                                if clean_phone == stored_clean:
                                    owner_id = uid
                                    break
                        
                        if owner_id:
                            logging.info(f"✅ Found owner for phone {phone} -> User ID: {owner_id}")
                        else:
                            logging.warning(f"❌ No owner found for phone {phone}")
                        
                        # Format and send messages
                        otp_display = f"<code>{otp}</code>" if otp != "N/A" else "Not found"
                        group_title = "📱 <b>New OTP!</b> ✨" if otp != "N/A" else "📱 <b>New Message!</b> ✨"
                        user_first_name = users_data.get(owner_id, {}).get('first_name', 'User') if owner_id else 'User'
                        
                        group_msg = (
                            f"<blockquote>{group_title}\n\n"
                            f"📞 <b>Number:</b> <code>{hide_number(phone)}</code>\n"
                            f"🌍 <b>Country:</b> {html_escape(sms_data.get('country', 'N/A'))}\n"
                            f"🆔 <b>Provider:</b> {html_escape(sms_data.get('provider', 'N/A'))}\n"
                            f"🔑 <b>OTP Code:</b> {otp_display}\n\n"
                            f"📝 <b>Full Message:</b>\n{html_escape(message) if message else '<i>(No message body)</i>'}</blockquote>\n\n"
                            f"{user_first_name} <b>🎉 You have earned ৳{SMS_AMOUNT:.4f} for this message!</b>"
                        )
                        
                        group_keyboard = InlineKeyboardMarkup([
                            [InlineKeyboardButton("Number Bot", url="https://t.me/SREOTPBOT"),
                             InlineKeyboardButton("Update Channel", url="https://t.me/SRFASTOTPNUMBER")]
                        ])

                        # Send to group
                        try:
                            await application.bot.send_message(
                                chat_id=GROUP_ID, 
                                text=group_msg, 
                                parse_mode=ParseMode.HTML, 
                                reply_markup=group_keyboard
                            )
                        except Exception as e:
                            logging.error(f"Failed to send SMS to group: {e}")

                        # Handle user-specific actions with enhanced tracking
                        if owner_id:
                            # Use UserManager for balance updates
                            UserManager.update_user_balance(owner_id, SMS_AMOUNT, "SMS Received")
                            new_sms_found_for_user = True

                            inbox_msg = (
                                f"<blockquote>{group_title}\n\n"
                                f"📞 <b>Number:</b> <code>{hide_number(phone)}</code>\n"
                                f"🌍 <b>Country:</b> {html_escape(sms_data.get('country', 'N/A'))}\n"
                                f"🆔 <b>Provider:</b> {html_escape(sms_data.get('provider', 'N/A'))}\n"
                                f"🔑 <b>OTP Code:</b> {otp_display}\n\n"
                                f"📝 <b>Full Message:</b>\n{html_escape(message) if message else '<i>(No message body)</i>'}</blockquote>\n\n"
                                f"{user_first_name} <b>🎉 You have earned ৳{SMS_AMOUNT:.4f} for this message!</b>\n"
                                f"💰 <b>Total Balance:</b> ৳{users_data.get(owner_id, {}).get('balance', 0) + SMS_AMOUNT:.2f}"
                            )
                            
                            try:
                                await application.bot.send_message(
                                    chat_id=owner_id, 
                                    text=inbox_msg, 
                                    parse_mode=ParseMode.HTML
                                )
                            except Exception as e:
                                logging.error(f"Failed to send inbox SMS to user {owner_id}: {e}")

                        sent_sms_keys.add(unique_key)
                    except Exception as e:
                        logging.error(f"Error processing SMS line: {e}")

            if new_sms_found_for_user:
                # Clear cache after updates
                smart_cache.clear_cache()
            
            save_sent_sms_keys(sent_sms_keys)

        except Exception as e:
            logging.error(f"Error in sms_watcher_task: {e}")
        
        await asyncio.sleep(10)


async def handle_text_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_state = context.user_data.get('state')
    if user_state == 'AWAITING_WITHDRAWAL_AMOUNT':
        await handle_withdrawal_amount(update, context)
        return
    if user_state == 'AWAITING_WITHDRAWAL_INFO':
        await handle_withdrawal_request(update, context)
        return

    if text == "🎁 Get Number":
        await handle_get_number(update, context)
    elif text == "👤 Account":
        await handle_account(update, context)
    elif text == "💰 Balance":
        await handle_balance(update, context)
    elif text == "💸 Withdraw":
        await handle_withdraw(update, context)
    elif text == "📋 Withdraw History":
        await handle_withdraw_history(update, context)
    else:
        # Handle any other text message with error and /start instruction
        # Only send error message in private chats (inbox), not in group chats
        if update.effective_chat.type == 'private':
            await update.message.reply_text(
                text="<b>❌ Error: Invalid message format</b>\n\n"
                     "<blockquote>I don't understand regular text messages. Please use /start to begin using this bot and try again.</blockquote>\n\n"
                     "<b>💡 Instructions:</b>\n"
                     "• Click /start to see available options\n"
                     "• Use the buttons provided by the bot\n"
                     "• Don't send regular text messages",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu_keyboard()
            )
        # For group chats, silently ignore unknown text messages

async def number_scraper_task():
    """Disabled - numbers scraped once at startup."""
    while not shutdown_event.is_set():
        await asyncio.sleep(1800)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and handle gracefully."""
    logging.error("Exception while handling an update:", exc_info=context.error)
    
    if isinstance(context.error, error.TimedOut):
        logging.warning("Telegram API timeout - temporary")
        return
    elif isinstance(context.error, error.NetworkError):
        logging.warning("Network error - connection issues")
        return
    elif isinstance(context.error, error.BadRequest):
        logging.warning(f"Bad request: {context.error}")
        return
    
    logging.error(f"Unhandled error: {context.error}")

async def main_bot_loop():
    """Main bot loop with optimized initialization."""
    global manager_instance
    try:
        load_config()
    except Exception as e:
        logging.critical(f"CRITICAL: Could not load config. {e}")
        PanelApp.show_error_static(f"Config Error: {e}\nPlease create a valid config.txt and restart.")
        return
        
    try:
        manager_instance = IvaSmsManager()
    except FileNotFoundError as e:
        if "chromedriver.exe" in str(e):
            logging.critical(f"CRITICAL: chromedriver.exe not found: {e}")
            PanelApp.show_error_static("ChromeDriver Error: chromedriver.exe not found!\n\nPlease:\n1. Place chromedriver.exe in the same folder as app.py\n2. Or in the dist folder if running as executable\n3. Restart the application")
            return
        else:
            raise

    # Configure application with optimized settings
    from telegram.request import HTTPXRequest
    
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30.0,
        write_timeout=30.0,
        connect_timeout=10.0,
        pool_timeout=10.0
    )
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).request(request).build()
    
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("update", broadcast_command))
    application.add_handler(CommandHandler("stats", admin_stats_command))
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    
    menu_buttons = ["🎁 Get Number", "👤 Account", "💰 Balance", "💸 Withdraw", "📋 Withdraw History"]
    menu_filter = filters.TEXT & filters.Regex(f'^({"|".join(re.escape(btn) for btn in menu_buttons)})$')
    application.add_handler(MessageHandler(menu_filter, handle_text_menu))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_menu))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logging.info("Bot started successfully.")

    sms_task = asyncio.create_task(sms_watcher_task(application))
    number_task = asyncio.create_task(number_scraper_task())
    
    await shutdown_event.wait()
    
    sms_task.cancel()
    number_task.cancel()
    try:
        await sms_task
        await number_task
    except asyncio.CancelledError:
        logging.info("Background tasks cancelled.")

    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    logging.info("Bot stopped gracefully.")

def run_bot_in_thread():
    """Run the bot and handle cleanup."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main_bot_loop())
    except Exception as e:
        logging.error(f"Error in bot thread: {e}", exc_info=True)
        PanelApp.show_error_static(f"Bot thread error: {e}")
    finally:
        global manager_instance
        if manager_instance:
            manager_instance.cleanup()
        if loop.is_running():
            loop.close()

# --- GUI Panel ---
class PanelApp(ctk.CTk):
    error_static_callback = None
    def __init__(self):
        super().__init__()
        self.title("Bot Control Panel")
        self.geometry("400x250")
        ctk.set_appearance_mode("dark")
        self.is_running = False
        PanelApp.error_static_callback = self.show_error
        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.start_bot_on_launch()

    def _create_widgets(self):
        self.status_label = ctk.CTkLabel(self, text="Bot is Running", font=("Consolas", 18, "bold"), text_color="#00E676")
        self.status_label.pack(pady=15)

        self.numbers_label = ctk.CTkLabel(self, text="Available Numbers: Loading...", font=("Consolas", 14))
        self.numbers_label.pack(pady=5)

        self.members_label = ctk.CTkLabel(self, text="Total Members: Loading...", font=("Consolas", 14))
        self.members_label.pack(pady=5, expand=True)

    def start_bot_on_launch(self):
        if not self.is_running:
            shutdown_event.clear()
            self.is_running = True
            self.bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
            self.bot_thread.start()
            self.update_number_count()
            self.update_member_count()

    def update_number_count(self):
        """Periodically updates the number count label in the GUI."""
        if self.is_running and manager_instance:
            try:
                count = manager_instance.get_available_number_count()
                self.numbers_label.configure(text=f"Available Numbers: {count}")
            except Exception as e:
                self.numbers_label.configure(text="Available Numbers: Error")
                logging.error(f"GUI update error: {e}")
        self.after(5000, self.update_number_count)

    def update_member_count(self):
        """Periodically updates the member count label in the GUI."""
        if self.is_running:
            try:
                users_data = load_json_data(USERS_FILE, {})
                total_members = len(users_data)
                self.members_label.configure(text=f"Total Members: {total_members}")
            except Exception as e:
                self.members_label.configure(text="Total Members: Error")
                logging.error(f"GUI member count error: {e}")
        self.after(5000, self.update_member_count)

    def show_error(self, msg):
        self.status_label.configure(text="Error", text_color="#FF0000")
        tkinter.messagebox.showerror("Bot Error", msg)

    @staticmethod
    def show_error_static(msg):
        if 'app' in globals() and app:
             app.after(0, lambda: app.show_error(msg))

    def on_closing(self):
        """Graceful shutdown."""
        logging.info("Shutdown initiated from GUI.")
        shutdown_event.set()
        if self.bot_thread:
            self.bot_thread.join(timeout=15)
        self.destroy()

if __name__ == "__main__":
    app = PanelApp()
    app.mainloop()