import requests

def get_status(url="https://www.baidu.com"):
    try:
        response = requests.get(url)
        return f"Website {url} status: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
    
print(get_status())