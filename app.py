import requests
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

class FastOTPChecker:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        self.lock = threading.Lock()
        
        # Remove SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def get_headers(self):
        """Get optimized headers"""
        return {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "origin": "https://pack.chromaawards.com",
            "referer": "https://pack.chromaawards.com/sign-in",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
    
    def check_single_number(self, phone):
        """Check single number quickly"""
        url = "https://pack.chromaawards.com/otp"
        
        # Clean and add + prefix
        clean_phone = ''.join(filter(str.isdigit, phone))
        formatted_phone = f"+{clean_phone}"
        
        payload = {"phoneNumber": formatted_phone}
        headers = self.get_headers()
        
        try:
            # Very short delay for speed
            time.sleep(random.uniform(0.1, 0.3))
            
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=8
            )
            
            # Get exact response
            result = {
                'phone': formatted_phone,
                'status_code': response.status_code,
                'response_text': response.text,
                'success': False
            }
            
            # Check if successful
            if response.status_code == 200:
                result['success'] = True
                try:
                    json_data = response.json()
                    result['json_response'] = json_data
                except:
                    pass
            
            return result
            
        except Exception as e:
            return {
                'phone': formatted_phone,
                'status_code': 0,
                'response_text': f"Error: {str(e)}",
                'success': False
            }
    
    def process_result(self, result):
        """Process and display result"""
        with self.lock:
            self.results.append(result)
            
            if result['success']:
                print(f"✅ SUCCESS: {result['phone']}")
                print(f"   Response: {result['response_text']}")
            else:
                print(f"❌ FAILED: {result['phone']} - Status: {result['status_code']}")
                print(f"   Response: {result['response_text']}")
    
    def run_fast_check(self, numbers, max_workers=10):
        """Run fast concurrent checking"""
        print(f"🚀 FAST CHECKING {len(numbers)} NUMBERS")
        print(f"⚡ Using {max_workers} concurrent workers")
        print("=" * 60)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_phone = {
                executor.submit(self.check_single_number, phone): phone 
                for phone in numbers
            }
            
            # Process as they complete
            completed = 0
            for future in as_completed(future_to_phone):
                try:
                    result = future.result()
                    self.process_result(result)
                    completed += 1
                    
                    # Show progress
                    if completed % 10 == 0:
                        elapsed = time.time() - start_time
                        print(f"📊 Progress: {completed}/{len(numbers)} | Time: {elapsed:.1f}s")
                        
                except Exception as exc:
                    phone = future_to_phone[future]
                    print(f"💥 ERROR: {phone} - {exc}")
        
        end_time = time.time()
        return end_time - start_time
    
    def save_detailed_results(self):
        """Save all detailed results"""
        timestamp = int(time.time())
        filename = f"detailed_results_{timestamp}.txt"
        
        with open(filename, "w") as f:
            f.write("DETAILED OTP CHECK RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            successful = [r for r in self.results if r['success']]
            failed = [r for r in self.results if not r['success']]
            
            f.write(f"TOTAL CHECKED: {len(self.results)}\n")
            f.write(f"SUCCESSFUL: {len(successful)}\n")
            f.write(f"FAILED: {len(failed)}\n\n")
            
            # Successful numbers
            if successful:
                f.write("✅ SUCCESSFUL NUMBERS:\n")
                for result in successful:
                    f.write(f"Phone: {result['phone']}\n")
                    f.write(f"Response: {result['response_text']}\n")
                    if 'json_response' in result:
                        f.write(f"JSON: {json.dumps(result['json_response'])}\n")
                    f.write("-" * 40 + "\n")
                f.write("\n")
            
            # Failed numbers
            if failed:
                f.write("❌ FAILED NUMBERS:\n")
                for result in failed:
                    f.write(f"Phone: {result['phone']}\n")
                    f.write(f"Status: {result['status_code']}\n")
                    f.write(f"Response: {result['response_text']}\n")
                    f.write("-" * 40 + "\n")
        
        return filename

def get_numbers_from_user():
    """Get phone numbers from terminal input"""
    print("📱 PHONE NUMBER INPUT")
    print("=" * 50)
    print("Enter phone numbers (without +)")
    print("You can enter:")
    print("1. Single number: 917834567890")
    print("2. Multiple numbers separated by space: 917834567890 918834567891")
    print("3. Multiple numbers separated by comma: 917834567890,918834567891")
    print("4. Range: 917834567000-917834567005")
    print("5. Exit: type 'done' or 'exit'")
    print("=" * 50)
    print("ℹ️  Script will automatically add + prefix")
    print("=" * 50)
    
    numbers = []
    
    while True:
        user_input = input("\nEnter numbers: ").strip()
        
        if user_input.lower() in ['done', 'exit', 'quit', '']:
            break
        
        if not user_input:
            continue
        
        # Process different input formats
        if '-' in user_input and len(user_input.split('-')) == 2:
            # Range input
            try:
                start, end = user_input.split('-')
                start = start.strip()
                end = end.strip()
                
                # Convert to integers for range, but keep as strings
                start_num = int(start)
                end_num = int(end)
                
                if start_num <= end_num:
                    for num in range(start_num, end_num + 1):
                        numbers.append(str(num))
                    print(f"✅ Added range: {start} to {end} ({end_num - start_num + 1} numbers)")
                else:
                    print("❌ Invalid range: start must be less than end")
            except ValueError:
                print("❌ Invalid range format. Use: start-end")
        
        elif ',' in user_input:
            # Comma separated
            new_numbers = [num.strip() for num in user_input.split(',') if num.strip()]
            numbers.extend(new_numbers)
            print(f"✅ Added {len(new_numbers)} numbers")
        
        elif ' ' in user_input:
            # Space separated
            new_numbers = [num.strip() for num in user_input.split() if num.strip()]
            numbers.extend(new_numbers)
            print(f"✅ Added {len(new_numbers)} numbers")
        
        else:
            # Single number
            numbers.append(user_input)
            print(f"✅ Added 1 number")
        
        print(f"📊 Total numbers so far: {len(numbers)}")
    
    return numbers

def main():
    checker = FastOTPChecker()
    
    # Get numbers from user input
    numbers = get_numbers_from_user()
    
    if not numbers:
        print("❌ No numbers entered!")
        return
    
    print(f"\n📱 Ready to check {len(numbers)} numbers")
    
    # Show preview of numbers with + prefix
    print("\n📋 Numbers to check (with + prefix):")
    for i, num in enumerate(numbers[:5]):
        print(f"  {i+1}. +{num}")
    if len(numbers) > 5:
        print(f"  ... and {len(numbers) - 5} more")
    
    # Confirm before starting
    confirm = input("\nStart checking? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes', '']:
        print("Cancelled!")
        return
    
    # Run fast check
    duration = checker.run_fast_check(numbers, max_workers=15)
    
    # Show summary
    successful = [r for r in checker.results if r['success']]
    failed = [r for r in checker.results if not r['success']]
    
    print("\n" + "=" * 60)
    print("🎯 QUICK SUMMARY")
    print("=" * 60)
    print(f"Total Numbers: {len(numbers)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Time Taken: {duration:.2f} seconds")
    print(f"Speed: {len(numbers)/duration:.2f} numbers/second")
    
    if successful:
        print(f"\n✅ SUCCESSFUL NUMBERS ({len(successful)}):")
        for result in successful[:10]:
            print(f"  {result['phone']}")
        if len(successful) > 10:
            print(f"  ... and {len(successful) - 10} more")
    
    # Save detailed results
    filename = checker.save_detailed_results()
    print(f"\n📄 Detailed results saved to: {filename}")

if __name__ == "__main__":
    main()
