# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from rune_manager import RuneManager
import traceback


app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])  # Enable CORS for all routes

def create_rune_manager(rpc_user, rpc_password, rpc_url, wallet_name="wallet"):
    """
    Dynamically create a RuneManager instance with provided credentials.
    """
    # Debug output
    print(f"RPC User: {rpc_user}")
    print(f"RPC Password: {rpc_password}")
    print(f"Formatted RPC URL: {rpc_url}")
    print(f"Wallet Name: {wallet_name}")

    return RuneManager(rpc_user, rpc_password, rpc_url)


@app.route('/mint_rune', methods=['POST'])
def mint_rune():
    try:
        # Check the content type
        if request.content_type != 'application/json':
            return 'Unsupported Media Type: Content-Type must be application/json', 415

        # Parse the JSON data
        data = request.json

        # Extract to_address and expiration_date
        to_address = data.get("to_address")
        expiration_date = data.get("expiration_date")

        # Extract RPC credentials
        rpc_user = data.get("rpcUser")
        rpc_password = data.get("rpcPassword")
        rpc_url = data.get("rpcUrl")

        # Log the received data for debugging
        print(f"To Address: {to_address}")
        print(f"Expiration Date: {expiration_date}")
        print(f"RPC User: {rpc_user}")
        print(f"RPC Password: {rpc_password}")
        print(f"RPC URL: {rpc_url}")

        # Validate required fields
        if not to_address or not expiration_date:
            return "Missing to_address or expiration_date", 400

        if not rpc_user or not rpc_password or not rpc_url:
            return "Missing RPC credentials", 400

        # Create the RuneManager instance
        rune_manager = create_rune_manager(rpc_user, rpc_password, rpc_url)

        # Perform the mint operation
        txid = rune_manager.mint_rune_with_expiration(to_address, expiration_date)

        if "Error" in txid:
            return "Error minting rune", 401
        return {"txid": txid}, 200
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return "Error processing request", 500


@app.route('/read_runes_from_user_wallet', methods=['GET'])
def read_runes_from_user_wallet():
    try:
        # Extract query parameters from the request
        rpc_user = request.args.get("rpcUser")  # Retrieves 'your_rpc_username'
        rpc_password = request.args.get("rpcPassword")  # Retrieves 'your_rpc_password'
        rpc_url = request.args.get("rpcUrl")  # Retrieves 'http://localhost:8332/wallet/wallet'

        # Create RuneManager instance
        rune_manager = create_rune_manager(rpc_user, rpc_password, rpc_url)

        # Read runes from the user's wallet
        runes_list = rune_manager.read_runes_from_wallet()
        if runes_list:
            return {"runes_list": runes_list}, 200
        else:
            return 'Error reading runes', 401
    except Exception as e:
        print(e)
        traceback.print_exc()
        return 'Error processing request', 500


@app.route('/read_runes_minted_by_user', methods=['GET'])
def read_runes_minted_by_user():
    try:
        # Extract query parameters from the request
        rpc_user = request.args.get("rpcUser")  # Retrieves 'your_rpc_username'
        rpc_password = request.args.get("rpcPassword")  # Retrieves 'your_rpc_password'
        rpc_url = request.args.get("rpcUrl")  # Retrieves 'http://localhost:8332/wallet/wallet'

        # Create RuneManager instance
        rune_manager = create_rune_manager(rpc_user, rpc_password, rpc_url)

        # Read runes minted by the user
        runes_list = rune_manager.read_runes_minted_by_user()
        if runes_list:
            return {"runes_minted": runes_list}, 200
        else:
            return 'Error reading runes', 401
    except Exception as e:
        print(e)
        traceback.print_exc()
        return 'Error processing request', 500



if __name__ == '__main__':
    app.run(port=5000, debug=True)


