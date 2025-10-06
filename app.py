import requests
import json

def test_single_number():
    """
    Test just one number and show everything
    """
    url = "https://pack.chromaawards.com/otp"
    
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "origin": "https://pack.chromaawards.com",
        "referer": "https://pack.chromaawards.com/sign-in",
    }
    
    # Test with one number
    test_number = "2250716635173"  # Change this to any number you want to test
    formatted_phone = f"+{test_number}"
    
    payload = {"phoneNumber": formatted_phone}
    
    print("=== API REQUEST DETAILS ===")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\n=== API RESPONSE ===")
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json=payload, 
            timeout=10,
            verify=False
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nRaw Response Text: {response.text}")
        
        # Try to parse JSON
        try:
            json_data = response.json()
            print(f"\nParsed JSON Response: {json.dumps(json_data, indent=2)}")
        except:
            print("\nCould not parse response as JSON")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    test_single_number()
