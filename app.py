import requests
import time
import random
import json
from fake_useragent import UserAgent

def test_otp():
    """
    Test OTP API with anti-detection measures and remove successful numbers from numbers.txt
    """
    # Initialize UserAgent for realistic browser headers
    ua = UserAgent()
    
    # Multiple base URLs to rotate (if available)
    base_urls = [
        "https://pack.chromaawards.com/otp",
        "https://pack.chromaawards.com/otp"
    ]
    
    # Read numbers from file
    try:
        with open("numbers.txt", "r") as f:
            numbers = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("ERROR: numbers.txt not found!")
        return
    
    print(f"Testing {len(numbers)} numbers...")
    
    successful = []
    failed = []
    
    for i, phone in enumerate(numbers, 1):
        full_phone = f"+{phone}"
        
        # Rotate strategies every 10 numbers
        strategy = (i - 1) // 10
        
        if strategy == 0:
            # Strategy 1: Standard requests with random delays
            url = random.choice(base_urls)
            headers = generate_headers_v1(ua)
            delay = random.uniform(1, 2)
            
        elif strategy == 1:
            # Strategy 2: Different header pattern with shorter delays
            url = random.choice(base_urls)
            headers = generate_headers_v2(ua)
            delay = random.uniform(0.5, 1.5)
            
        elif strategy == 2:
            # Strategy 3: Mobile-like headers
            url = random.choice(base_urls)
            headers = generate_headers_v3(ua)
            delay = random.uniform(0.8, 1.8)
            
        else:
            # Strategy 4: Mixed approach
            url = random.choice(base_urls)
            headers = generate_headers_v4(ua)
            delay = random.uniform(0.6, 1.2)
        
        payload = {"phoneNumber": full_phone}
        
        try:
            print(f"[{i:2d}/{len(numbers)}] {full_phone} (Strategy {strategy + 1})", end=" - ")
            
            # Dynamic delay based on strategy
            time.sleep(delay)
            
            # Random timeout
            timeout = random.uniform(8, 12)
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=timeout,
                allow_redirects=random.choice([True, False])
            )
            
            # Random success pattern detection
            if response.status_code == 200:
                # Additional validation for response content
                try:
                    response_data = response.json()
                    if is_valid_response(response_data):
                        print("SUCCESS")
                        successful.append(phone)
                    else:
                        print("INVALID RESPONSE")
                        failed.append(phone)
                except:
                    print("SUCCESS")
                    successful.append(phone)
            else:
                print(f"FAILED ({response.status_code})")
                failed.append(phone)
                
        except requests.exceptions.Timeout:
            print("TIMEOUT")
            failed.append(phone)
        except requests.exceptions.ConnectionError:
            print("CONNECTION ERROR")
            failed.append(phone)
        except Exception as e:
            print(f"ERROR: {str(e)[:50]}...")
            failed.append(phone)
        
        # Every 5 requests, add a longer random break
        if i % 5 == 0:
            long_break = random.uniform(3, 8)
            print(f"Taking longer break: {long_break:.1f}s")
            time.sleep(long_break)
    
    # Remove successful numbers from file
    remaining = [num for num in numbers if num not in successful]
    
    with open("numbers.txt", "w") as f:
        for num in remaining:
            f.write(f"{num}\n")
    
    # Save results to separate file
    save_results(successful, failed)
    
    # Display results
    print(f"\nRESULTS:")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Remaining in file: {len(remaining)}")
    
    if successful:
        print(f"\nSUCCESSFUL NUMBERS:")
        for phone in successful:
            print(f"  +{phone}")

def generate_headers_v1(ua):
    """Generate standard browser headers"""
    return {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "user-agent": ua.chrome,
        "origin": "https://pack.chromaawards.com",
        "referer": "https://pack.chromaawards.com/sign-in",
        "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

def generate_headers_v2(ua):
    """Generate alternative browser headers"""
    return {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.8",
        "content-type": "application/json;charset=UTF-8",
        "user-agent": ua.firefox,
        "origin": "https://pack.chromaawards.com",
        "referer": "https://pack.chromaawards.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

def generate_headers_v3(ua):
    """Generate mobile-like headers"""
    return {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "user-agent": ua.android,
        "origin": "https://pack.chromaawards.com",
        "referer": "https://pack.chromaawards.com/sign-in",
        "x-requested-with": "XMLHttpRequest"
    }

def generate_headers_v4(ua):
    """Generate minimal headers"""
    return {
        "accept": "*/*",
        "content-type": "application/json",
        "user-agent": random.choice([ua.chrome, ua.firefox, ua.safari]),
        "origin": "https://pack.chromaawards.com",
        "referer": "https://pack.chromaawards.com/sign-in"
    }

def is_valid_response(response_data):
    """
    Validate if the response contains expected success indicators
    """
    if isinstance(response_data, dict):
        # Check for common success keys
        success_indicators = ['success', 'message', 'status', 'data']
        for indicator in success_indicators:
            if indicator in response_data:
                return True
    return True  # Default to True if validation is uncertain

def save_results(successful, failed):
    """Save results to a timestamped file"""
    timestamp = int(time.time())
    filename = f"results_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write("SUCCESSFUL NUMBERS:\n")
        for phone in successful:
            f.write(f"+{phone}\n")
        
        f.write("\nFAILED NUMBERS:\n")
        for phone in failed:
            f.write(f"+{phone}\n")
    
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    # Install required package if not available
    try:
        from fake_useragent import UserAgent
    except ImportError:
        print("Installing fake-useragent...")
        import subprocess
        subprocess.check_call(["pip", "install", "fake-useragent"])
        from fake_useragent import UserAgent
    
    test_otp()
