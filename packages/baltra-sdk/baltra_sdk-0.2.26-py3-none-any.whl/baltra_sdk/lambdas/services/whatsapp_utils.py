import requests
import json


def get_account_config(wa_id_system, settings):
    """Get WhatsApp account configuration.
    
    Args:
        wa_id_system: WhatsApp ID of the system/company
        settings: Settings object with ACCESS_TOKEN, META_APP_SECRET, and VERSION attributes
    
    Returns:
        dict: Account configuration with access_token, app_secret, account_type, and version
    """
    return {
        "access_token": settings.ACCESS_TOKEN,
        "app_secret": settings.META_APP_SECRET,
        "account_type": "PRIMARY",
        "version": settings.VERSION
    }


def log_http_response(response):
    """Log HTTP response details."""
    print(f"Status: {response.status_code}")
    print(f"Content-type: {response.headers.get('content-type')}")
    print(f"Body: {response.text}")


def send_message(data, sender, settings, campaign_id=None):
    """Send a message via WhatsApp Business API.
    
    Args:
        data: JSON string or dict with the message data
        sender: WhatsApp ID of the sender
        settings: Settings object with ACCESS_TOKEN, META_APP_SECRET, and VERSION attributes
        campaign_id: Optional campaign ID
    
    Returns:
        requests.Response: HTTP response from the API, or None if error
    """
    if data is None:
        print(f"Cannot send message: data parameter is None for sender {sender}")
        return None
        
    account_config = get_account_config(sender, settings)
    if not account_config:
        print(f"[Account: UNKNOWN] Could not determine account configuration for sender: {sender}")
        return None
    
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {account_config['access_token']}",
    }

    url = f"https://graph.facebook.com/{account_config['version']}/{sender}/messages"
    
    try:
        print(f'[Account: {account_config["account_type"]}] Whatsapp Message Structure: {data}')
        response = requests.post(
            url, data=data, headers=headers, timeout=30
        )
        response.raise_for_status()
    except requests.Timeout:
        print(f"[Account: {account_config['account_type']}] Timeout occurred while sending message")
        log_http_response(response)
        return response
    except requests.RequestException as e:
        log_http_response(response)        
        try:
            wa_id = json.loads(data)["to"] if data else "unknown"
        except (json.JSONDecodeError, TypeError, KeyError):
            wa_id = "unknown"
        
        print(f'[Account: {account_config["account_type"]}] Storing rejected message for wa_id {wa_id}')
        return response
    else:
        log_http_response(response)
        
        try:
            wa_id = json.loads(data)["to"] if data else "unknown"
        except (json.JSONDecodeError, TypeError, KeyError):
            wa_id = "unknown"
        
        print(f'[Account: {account_config["account_type"]}] Message sent successfully to wa_id {wa_id}')
        return response

