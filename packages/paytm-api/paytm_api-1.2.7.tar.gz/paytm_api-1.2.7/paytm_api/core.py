import hmac
import hashlib
import json
import requests

def verify_payment(mid: str, order_id: str) -> dict:
    mid = str(mid).strip()
    order_id = str(order_id).strip()

    if not mid or not order_id:
        return {"RESPCODE": "335", "RESPMSG": "Missing parameters 'mid' or 'order_id'"}

    if len(mid) >= 36 or len(order_id) <= 6:
        return {"RESPCODE": "335", "RESPMSG": "Invalid parameters."}

    try:
        data = {"MID": mid, "ORDERID": order_id}
        json_data = json.dumps(data)

        checksum = hmac.new(mid.encode(), json_data.encode(), hashlib.sha256).hexdigest()

        url = f"https://paytm-api.litedns.xyz/?mid={mid}&oid={order_id}"

        response = requests.get(url, timeout=10)
        return response.json() if response.ok else {"RESPCODE": "500", "RESPMSG": "Failed to contact Paytm"}

    except Exception as e:
        return {"RESPCODE": "500", "RESPMSG": str(e)}
