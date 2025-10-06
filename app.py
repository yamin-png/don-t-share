import requests
import time
import random

def test_otp():
    """
    Test OTP API and remove successful numbers from numbers.txt
    """
    url = "https://pack.chromaawards.com/otp"
    
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 OPR/122.0.0.0",
        "origin": "https://pack.chromaawards.com",
        "referer": "https://pack.chromaawards.com/sign-in"
    }
    
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
        payload = {"phoneNumber": full_phone}
        
        try:
            print(f"[{i:2d}/{len(numbers)}] {full_phone}", end=" - ")
            
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("SUCCESS")
                successful.append(phone)
            else:
                print(f"FAILED ({response.status_code})")
                failed.append(phone)
                
        except Exception as e:
            print(f"ERROR: {e}")
            failed.append(phone)
    
    # Remove successful numbers from file
    remaining = [num for num in numbers if num not in successful]
    
    with open("numbers.txt", "w") as f:
        for num in remaining:
            f.write(f"{num}\n")
    
    # Results
    print(f"\nRESULTS:")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Remaining in file: {len(remaining)}")
    
    if successful:
        print(f"\nSUCCESSFUL NUMBERS:")
        for phone in successful:
            print(f"  +{phone}")

if __name__ == "__main__":
    test_otp()

