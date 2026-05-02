from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

API_URL = "https://coreregistry.in/api/v1/vehicle"
OWNER_MSG = "@PurelyYour | Buy Instantly at the Best Price"

# KEY = "1month"
HARDCODED_KEY = "1month"

# Expires 30 days from deployment
KEY_EXPIRY = datetime(2026, 6, 2)  # 👈 1 month from today (May 2)

@app.route("/")
def home():
    remaining_days = (KEY_EXPIRY - datetime.now()).days
    return jsonify({
        "status": "online",
        "owner": OWNER_MSG,
        "key": "1month",
        "expires_in_days": remaining_days,
        "expiry_date": KEY_EXPIRY.strftime('%Y-%m-%d')
    })

@app.route("/vehicle", methods=["GET"])
def vehicle_lookup():
    api_key = request.args.get("key")
    
    # Check if key expired
    if datetime.now() > KEY_EXPIRY:
        return jsonify({
            "success": False,
            "owner": OWNER_MSG,
            "message": "Key Expired"
        }), 401
    
    # Check key = "1month"
    if api_key != HARDCODED_KEY:
        return jsonify({
            "success": False,
            "owner": OWNER_MSG,
            "message": "Invalid Key"
        }), 401

    reg_no = request.args.get("reg")

    if not reg_no:
        return jsonify({
            "success": False,
            "owner": OWNER_MSG,
            "message": "Registration number required"
        }), 400

    try:
        # This is where vehicle data comes from
        response = requests.get(
            API_URL,
            params={"reg": reg_no},
            timeout=15
        )

        if response.status_code != 200:
            return jsonify({
                "success": False,
                "owner": OWNER_MSG,
                "message": "Gateway connection failed"
            }), response.status_code

        data = response.json()

        if data.get("registry_status") != "AUTHORIZED_ACCESS_GRANTED":
            return jsonify({
                "success": False,
                "owner": OWNER_MSG,
                "message": "Vehicle not found"
            }), 404

        payload = data.get("registry_payload", {})
        identity = payload.get("identity_info", {})
        machine = payload.get("machine_specifications", {})

        # Vehicle response - YES it shows all this data
        result = {
            "success": True,
            "owner": OWNER_MSG,
            "data": {
                "registration_id": identity.get("registration_id"),
                "owner_legal_name": identity.get("owner_legal_name"),
                "registered_contact": identity.get("registered_contact"),
                "rto_jurisdiction": identity.get("rto_jurisdiction"),
                "fuel_type": machine.get("fuel_type"),
                "engine_serial": machine.get("engine_serial"),
                "chassis_id": machine.get("chassis_id")
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "owner": OWNER_MSG,
            "message": f"Error: {str(e)}"
        }), 500
