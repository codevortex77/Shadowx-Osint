from flask import Flask, request, jsonify
import requests
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)

API_URL = "https://coreregistry.in/api/v1/vehicle"
OWNER_MSG = "@PurelyYour | Buy Instantly at the Best Price"

# Generate a key valid for 30 days
def generate_key():
    expiry = datetime.now() + timedelta(days=30)
    secret = f"purelyyour{expiry.strftime('%Y%m%d')}"
    return hashlib.sha256(secret.encode()).hexdigest(), expiry

# Validate the key
def validate_key(key):
    valid_key, expiry = generate_key()
    if key == valid_key and datetime.now() < expiry:
        return True
    return False

# Initial key (will expire in 30 days from now)
KEY, EXPIRY = generate_key()

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "owner": OWNER_MSG
    })

@app.route("/get-key", methods=["GET"])
def get_key():
    return jsonify({
        "key": KEY,
        "expiry": EXPIRY.strftime('%Y-%m-%d %H:%M:%S'),
        "message": "This key is valid for 30 days"
    })

@app.route("/vehicle", methods=["GET"])
def vehicle_lookup():
    api_key = request.args.get("key")
    
    # Check if key is provided
    if not api_key:
        return jsonify({
            "success": False,
            "owner": OWNER_MSG,
            "message": "API Key Required"
        }), 401
    
    # Validate the key
    if not validate_key(api_key):
        return jsonify({
            "success": False,
            "owner": OWNER_MSG,
            "message": "Key Expired"
        }), 401

    reg_no = request.args.get("reg")

    if not reg_no:
        return jsonify({
            "success": False,
            "owner": OWNER_MSG,
            "message": "Registration number required"
        }), 400

    try:
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

        result = {
            "success": True,
            "owner": OWNER_MSG,
            "registration_id": identity.get("registration_id"),
            "owner_legal_name": identity.get("owner_legal_name"),
            "registered_contact": identity.get("registered_contact"),
            "rto_jurisdiction": identity.get("rto_jurisdiction"),
            "fuel_type": machine.get("fuel_type"),
            "engine_serial": machine.get("engine_serial"),
            "chassis_id": machine.get("chassis_id")
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "owner": OWNER_MSG,
            "message": str(e)
        }), 500
