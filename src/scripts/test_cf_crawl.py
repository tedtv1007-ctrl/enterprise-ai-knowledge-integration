import os
import json
import requests
import time

def load_secrets():
    path = "/home/node/.openclaw/workspace/milk-secrets-repo/cloudflare.json"
    with open(path, 'r') as f:
        return json.load(f)

def start_crawl(url):
    secrets = load_secrets()
    account_id = secrets.get("account id")
    api_token = secrets.get("api token")
    
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "url": url,
        "render": True,
        "markdown": True
    }
    
    print(f"[*] Starting crawl for: {url}")
    response = requests.post(endpoint, headers=headers, json=data)
    
    if response.status_code == 201 or response.status_code == 200:
        job_id = response.json().get("result", {}).get("id")
        print(f"[+] Crawl job created. Job ID: {job_id}")
        return job_id
    else:
        print(f"[!] Failed to start crawl: {response.status_code}")
        print(response.text)
        return None

def check_status(job_id):
    secrets = load_secrets()
    account_id = secrets.get("account id")
    api_token = secrets.get("api token")
    
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl/{job_id}"
    
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        result = response.json().get("result", {})
        status = result.get("status")
        print(f"[*] Job Status: {status}")
        return result
    else:
        print(f"[!] Failed to check status: {response.status_code}")
        return None

if __name__ == "__main__":
    # Test with Cloudflare Blog
    test_url = "https://blog.cloudflare.com/tag/browser-rendering/"
    job_id = start_crawl(test_url)
    
    if job_id:
        print("[*] Waiting for results (polling every 10s)...")
        while True:
            result = check_status(job_id)
            if result and result.get("status") in ["completed", "failed"]:
                print(f"[+] Final Result: {json.dumps(result, indent=2)}")
                break
            time.sleep(10)
