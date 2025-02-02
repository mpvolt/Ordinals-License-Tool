import uuid
import requests
from datetime import datetime
import json
import time
import hashlib
import base64
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import binascii



class RuneManager:
    def __init__(self, rpc_user, rpc_password, url):
        url = url.split('//')[1]
        self.url = f'http://{rpc_user}:{rpc_password}@{url}'



    # Function to make an RPC call
    def rpc_request(self, method, params=[]):
        headers = {'content-type': 'application/json'}
        payload = json.dumps({"method": method, "params": params, "jsonrpc": "2.0", "id": 1})

        try:
            # Add timeout to the request
            response = requests.post(self.url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()  # Check for HTTP errors
            return response.json()
        except requests.exceptions.Timeout:
            print("Request timed out after 10 seconds")
            return {"error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return {"error": str(e)}

    # Function to create unique metadata for each Rune
    def create_rune_metadata(self):

        # Generate a unique UUID for each Rune
        unique_id = str(uuid.uuid4())  
        
        # Get the current time as a Unix timestamp
        issued_timestamp = datetime.today().strftime('%Y-%m-%d')#%H:%M:%S')
        #issued_timestamp = int(time.time())  # current time as a Unix timestamp

        # Create metadata with dynamic dates
        metadata = {
            "rune_id": unique_id,
            "issued_date": issued_timestamp,
        }

        return metadata

# Function to create unique metadata for each Rune
    def create_rune_metadata_with_expiration(self, expiration_date):

        # Generate a unique UUID for each Rune
        unique_id = str(uuid.uuid4())
        unique_id = unique_id[:8]

        # Create metadata with dynamic dates
        metadata = {
            "rune_id": unique_id,
            "expiration_date": expiration_date,
        }

        return metadata

    def mint_rune(self, to_address):
        # Create Rune metadata and convert it to hexadecimal
        metadata = self.create_rune_metadata()
        metadata_bytes = json.dumps(metadata).encode('utf-8')  # Convert metadata to JSON string, then to bytes
        metadata_hex = metadata_bytes.hex()  # Convert bytes to hexadecimal format

        # Get UTXOs (inputs) from the wallet, regardless of address
        response = self.rpc_request('listunspent')
        utxos = response['result']

        if not utxos:
            return("Error: no UTXOs available to spend.")
            

        # Select UTXOs as inputs for the transaction until the required amount is reached
        inputs = []
        total_utxo_amount = 0
        for utxo in utxos:
            inputs.append({"txid": utxo["txid"], "vout": utxo["vout"]})
            total_utxo_amount += utxo["amount"]
            if total_utxo_amount >= 0.0001:  # Stop when we have enough to cover the transaction
                break

        # Define amounts
        send_amount = 0.00001  # Amount of BTC to send with the Rune
        fee = 0.00001         # Estimated fee

        total_required = round(send_amount + fee, 8)
        change_amount = round(total_utxo_amount - total_required, 8)

        # Check if total UTXO amount is sufficient to cover the required amount
        if total_utxo_amount < total_required:
            return(f"Error: Insufficient UTXO amount. Available: {total_utxo_amount} BTC, Required: {total_required} BTC.")
              # Exit if the total UTXO amount is insufficient

        # Check if change amount is above the dust limit (around 0.00000546 BTC)
        if change_amount < 0.00000546:
            return(f"Error: change amount {change_amount} is below the dust threshold.")

        # Outputs:
        # 1. Send the specified amount to the Rune address.
        # 2. Send the remaining change back to one of the wallet's addresses (e.g., the first UTXO's address).
        # 3. Include the OP_RETURN data for the Rune's metadata.
        outputs = {
            to_address: send_amount,                 # Send a small amount to the Rune address
            utxos[0]["address"]: change_amount,      # Change back to the first UTXO's address
            "data": metadata_hex,                    # OP_RETURN with Rune metadata (no BTC amount needed here)
        }

        # Create the raw transaction
        response = self.rpc_request('createrawtransaction', [inputs, outputs])

        # Check for errors
        if 'error' in response and response['error'] is not None:
            return(f"Error creating raw transaction: {response['error']}")
        else:
            raw_tx = response['result']
            print(f"Raw transaction created: {raw_tx}")

        # Fund the transaction to automatically add fee
        response = self.rpc_request('fundrawtransaction', [raw_tx])

        # Check for errors during funding
        if 'error' in response and response['error'] is not None:
            return(f"Error funding transaction: {response['error']}")
        else:
            funded_tx = response['result']['hex']
            print(f"Funded transaction: {funded_tx}")

        # Sign the funded transaction with the wallet's private keys
        response = self.rpc_request('signrawtransactionwithwallet', [funded_tx])

        # Check for errors during signing
        if 'error' in response and response['error'] is not None:
            return(f"Error signing transaction: {response['error']}")
            
        else:
            signed_tx = response['result']['hex']
            print(f"Signed transaction: {signed_tx}")

        # Broadcast the transaction to the Bitcoin network
        response = self.rpc_request('sendrawtransaction', [signed_tx])

        # Check for errors during broadcasting
        if 'error' in response and response['error'] is not None:
            return f"Error minting Rune: {response['error']}"
        else:
            txid = response['result']
            print(f"Rune minted with TXID: {txid}")
            return txid

    def mint_rune_with_expiration(self, to_address, expiration_date):
        # Create Rune metadata and convert it to hexadecimal
        metadata = self.create_rune_metadata_with_expiration(expiration_date)
        metadata_bytes = json.dumps(metadata).encode('utf-8')  # Convert metadata to JSON string, then to bytes
        metadata_hex = metadata_bytes.hex()  # Convert bytes to hexadecimal format

        # Get UTXOs (inputs) from the wallet, regardless of address
        response = self.rpc_request('listunspent')
        utxos = response['result']

        if not utxos:
            print("No UTXOs available to spend.")
            return

        # Select UTXOs as inputs for the transaction until the required amount is reached
        inputs = []
        total_utxo_amount = 0
        for utxo in utxos:
            inputs.append({"txid": utxo["txid"], "vout": utxo["vout"]})
            total_utxo_amount += utxo["amount"]
            if total_utxo_amount >= 0.0001:  # Stop when we have enough to cover the transaction
                break

        # Define amounts
        send_amount = 0.00001  # Amount of BTC to send with the Rune
        fee = 0.00001         # Estimated fee

        total_required = round(send_amount + fee, 8)
        change_amount = round(total_utxo_amount - total_required, 8)

        # Check if total UTXO amount is sufficient to cover the required amount
        if total_utxo_amount < total_required:
            print(f"Insufficient UTXO amount. Available: {total_utxo_amount} BTC, Required: {total_required} BTC.")
            return  # Exit if the total UTXO amount is insufficient

        # Check if change amount is above the dust limit (around 0.00000546 BTC)
        if change_amount < 0.00000546:
            print(f"Change amount {change_amount} is below the dust threshold.")
            return

        # Outputs:
        # 1. Send the specified amount to the Rune address.
        # 2. Send the remaining change back to one of the wallet's addresses (e.g., the first UTXO's address).
        # 3. Include the OP_RETURN data for the Rune's metadata.
        outputs = {
            to_address: send_amount,                 # Send a small amount to the Rune address
            utxos[0]["address"]: change_amount,      # Change back to the first UTXO's address
            "data": metadata_hex,                    # OP_RETURN with Rune metadata (no BTC amount needed here)
        }

        # Create the raw transaction
        response = self.rpc_request('createrawtransaction', [inputs, outputs])

        # Check for errors
        if 'error' in response and response['error'] is not None:
            print(f"Error creating raw transaction: {response['error']}")
            return
        else:
            raw_tx = response['result']
            print(f"Raw transaction created: {raw_tx}")

        # Fund the transaction to automatically add fee
        response = self.rpc_request('fundrawtransaction', [raw_tx])

        # Check for errors during funding
        if 'error' in response and response['error'] is not None:
            print(f"Error funding transaction: {response['error']}")
            return
        else:
            funded_tx = response['result']['hex']
            print(f"Funded transaction: {funded_tx}")

        # Sign the funded transaction with the wallet's private keys
        response = self.rpc_request('signrawtransactionwithwallet', [funded_tx])

        # Check for errors during signing
        if 'error' in response and response['error'] is not None:
            print(f"Error signing transaction: {response['error']}")
            return
        else:
            signed_tx = response['result']['hex']
            print(f"Signed transaction: {signed_tx}")

        # Broadcast the transaction to the Bitcoin network
        response = self.rpc_request('sendrawtransaction', [signed_tx])

        # Check for errors during broadcasting
        if 'error' in response and response['error'] is not None:
            print(f"Error minting Rune: {response['error']}")
            return ''
        else:
            txid = response['result']
            print(f"Rune minted with TXID: {txid}")
            return txid

    # Function to decode hex-encoded Rune metadata
    def decode_rune_metadata(self, hex_data):
        try:
            metadata_bytes = bytes.fromhex(hex_data)
            metadata_json = metadata_bytes.decode('utf-8')
            metadata = json.loads(metadata_json)
            return metadata
        except Exception as e:
            #print(f"Error decoding metadata: {e}")
            return None

    # Fetch transaction data from Blockstream's API
    def fetch_tx_data(self, txid):
        try:
            # Use a public API to get the transaction data
            response = requests.get(f'https://blockstream.info/api/tx/{txid}')
            
            # Check if the request was successful
            if response.status_code == 200:

                # Ensure it's in JSON format before calling .json()
                if 'application/json' in response.headers.get('Content-Type', ''):
                    time.sleep(1)
                    return response.json()
                else:
                    print("Response is not in JSON format.")
                    return None
            else:
                return None

        except Exception as e:
            print(f"Error fetching tx data for {txid}: {str(e)}")
            return None

    
    def check_network_type(self):
        # Query the blockchain info to determine which network we're on
        response = self.rpc_request('getblockchaininfo')

        if 'error' in response and response['error'] is not None:
            print(f"Error fetching blockchain info: {response['error']}")
            return None
        
        chain = response['result']['chain']

        # Return 'mainnet' or 'testnet' based on the chain value
        if chain == 'main':
            #print("Running on mainnet.")
            return 'mainnet'
        elif chain == 'test':
            #print("Running on testnet.")
            return 'testnet'
        elif chain == 'regtest':
            #print("Running on regtest.")
            return 'regtest'
        else:
            print(f"Running on an unknown network: {chain}")
            return 'unknown'


    def lock_utxo(self, txid, vout):
        # Get list of currently locked UTXOs
        locked_utxos_response = self.rpc_request('listlockunspent')
        
        if 'error' in locked_utxos_response and locked_utxos_response['error'] is not None:
            print(f"Error fetching locked UTXOs: {locked_utxos_response['error']}")
            return

        locked_utxos = locked_utxos_response['result']
        
        # Convert locked UTXOs to a set of tuples (txid, vout)
        locked_utxo_tuples = {(utxo['txid'], utxo['vout']) for utxo in locked_utxos}

        # Check if the UTXO is already locked
        utxo_to_lock = (txid, vout)
        if utxo_to_lock not in locked_utxo_tuples:
            # Lock the UTXO if it is not already locked
            self.rpc_request('lockunspent', [False, [{"txid": txid, "vout": vout}]])
            #rint(f"Locked UTXO: {txid}, vout: {vout}")

    def get_sent_transactions(self, address):
        """
        Get all transactions sent by the user's wallet address.
        """
        try:
            # Fetch all transactions for the wallet from Blockstream's API
            response = requests.get(f'https://blockstream.info/api/address/{address}/txs')
            if response.status_code == 200:
                transactions = response.json()
                
                sent_transactions = []
                for tx in transactions:
                    # Only include transactions where the address was a sender
                    for input in tx.get('vin', []):
                        if input.get('prevout', {}).get('scriptpubkey_address') == address:
                            sent_transactions.append(tx['txid'])
                            break  # Move to the next transaction once we've identified it as a sent tx

                return sent_transactions
            else:
                print(f"Failed to fetch transactions for address {address}")

        except Exception as e:
            print(f"Error fetching transactions for address {address}: {str(e)}")
            return []

    def get_transactions_with_rune(self, sent_txids):
        """
        Get a list of all transactions with OP_RETURN data and associated recipient address.
        """
        op_return_transactions = []

        for txid in sent_txids:
            tx_data = self.fetch_tx_data(txid)
            if tx_data:
                rune_metadata, recipient_address = self.extract_rune_data(tx_data)
                block_time = tx_data.get('status', {}).get('block_time', None)
                # Only append if both OP_RETURN data and a recipient address are found
                if rune_metadata and recipient_address:
                    op_return_transactions.append({
                        "txid": txid,
                        "rune_metadata": rune_metadata,
                        "recipient": recipient_address,
                        "block_time": block_time
                    })

        return op_return_transactions


    def extract_rune_data(self, tx_data):
        """
        Extract rune metadata and recipient address from a transaction's outputs.
        """
        rune_metadata = None
        recipient_address = None

        for output in tx_data.get("vout", []):
            scriptpubkey_type = output.get("scriptpubkey_type")

            if scriptpubkey_type == "op_return":
                rune_metadata = self.parse_op_return_data(output.get('scriptpubkey'))
            elif scriptpubkey_type in ["v0_p2wpkh", "v0_p2wsh"]:
                recipient_address = output.get("scriptpubkey_address")

        return rune_metadata, recipient_address


    def parse_op_return_data(self, scriptpubkey):
        """
        Parse OP_RETURN data from scriptpubkey, accounting for length opcodes.
        """
        # Ensure the scriptpubkey is valid and starts with '6a'
        if not scriptpubkey or not scriptpubkey.startswith('6a') or len(scriptpubkey) <= 6:
            return f"Invalid OP_RETURN script: {scriptpubkey}"

        try:
            # Remove the '6a' prefix
            op_return_hex_data = scriptpubkey[2:]
            #print(f"After removing '6a': {op_return_hex_data}")

            # Handle potential length prefixes
            if op_return_hex_data.startswith('4c'):  # Single-byte length prefix
                op_return_hex_data = op_return_hex_data[2:]
            elif op_return_hex_data.startswith('4d'):  # Two-byte length prefix
                op_return_hex_data = op_return_hex_data[4:]

            #print(f"After handling length prefixes: {op_return_hex_data}")

            # Decode hex to bytes
            try:
                decoded_bytes = binascii.unhexlify(op_return_hex_data)
            except binascii.Error as e:
                return f"Error decoding hex: {e}"

            # Decode bytes to UTF-8 string
            try:
                ascii_data = decoded_bytes.decode("utf-8")
            except UnicodeDecodeError as e:
                return f"Error decoding to UTF-8: {e}"

            #print(f"Decoded ASCII data: {ascii_data}")

            # Locate the start of the JSON object
            json_start = ascii_data.find('{')
            if json_start == -1:
                return f"No JSON object found in data: {ascii_data}"

            # Extract the JSON string
            json_data = ascii_data[json_start:]
            #print(f"Extracted JSON data: {json_data}")

            # Parse JSON data
            try:
                rune_metadata = json.loads(json_data)
                if rune_metadata.get('expiration_date'):
                    expiration_date = datetime.strptime(rune_metadata.get('expiration_date'), '%Y-%m-%d')
                    rune_metadata["expiration_date"] = expiration_date.strftime('%Y-%m-%d')

                #If not, default licence length is 1 year
                elif rune_metadata.get('issued_date'):
                    issue_date = datetime.strptime(rune_metadata.get('issued_date'), '%Y-%m-%d')
                    expiration_date = issue_date.replace(year=issue_date.year + 1)
                    rune_metadata["expiration_date"] = expiration_date.strftime('%Y-%m-%d')

                # Only include if not expired
                if expiration_date > datetime.now():
                    rune_metadata = {
                        "Rune ID": rune_metadata['rune_id'],
                        "Expiration Date": rune_metadata.get('expiration_date'),
                    }
                return rune_metadata
            except json.JSONDecodeError as e:
                return f"Invalid JSON data: {ascii_data}, Error: {e}"

        except Exception as e:
            return f"Error parsing OP_RETURN data: {e}"

        return None

    


    def read_runes_minted_by_user(self):
        # Step 1: Fetch all wallet addresses using listreceivedbyaddress or getaddressesbylabel
        response = self.rpc_request('listreceivedbyaddress', [0, True])
        wallet_addresses = [entry['address'] for entry in response['result']]
        if not wallet_addresses:
            print("No addresses found in the current wallet.")
            return ''

        # Dictionary to store Runes keyed by txid to avoid duplication
        runes_found = {}
        sent_transactions = []
        for address in wallet_addresses:
            sent_tx = self.get_sent_transactions(address)
            if sent_tx:
                sent_transactions += sent_tx

        sent_transactions_with_runes = self.get_transactions_with_rune(sent_transactions)
        return sent_transactions_with_runes
        
        
    def read_runes_from_wallet(self):
        # Step 1: Fetch all wallet addresses using listreceivedbyaddress or getaddressesbylabel
        response = self.rpc_request('listreceivedbyaddress', [0, True])
        wallet_addresses = [entry['address'] for entry in response['result']]

        if not wallet_addresses:
            print("No addresses found in the current wallet.")
            return

        # Dictionary to store Runes keyed by txid to avoid duplication
        runes_found = {}

        # Cache network type for optimization
        network_type = self.check_network_type()

        # Step 2: Fetch transactions based on network type
        transactions = []
        if network_type in ['testnet', 'regtest']:
            response = self.rpc_request('listtransactions', ["*", 1000, 0, True])
            transactions = response['result']
        elif network_type == 'mainnet':
            # Consolidate listunspent and listlockunspent
            response = self.rpc_request('listunspent')
            utxos = response['result']
            response = self.rpc_request('listlockunspent')
            locked_utxos = response['result']
            combined_utxos = utxos + [{"txid": utxo['txid'], "vout": utxo['vout']} for utxo in locked_utxos]

            # Parallel fetch transaction details using threads
            with ThreadPoolExecutor() as executor:
                tx_details_list = list(executor.map(lambda utxo: self.fetch_tx_data(utxo['txid']), combined_utxos))
                transactions.extend(filter(None, tx_details_list))  # Remove any None results from failed fetches

        if not transactions:
            print("No transactions found.")
            return

        # Step 3: Iterate through each transaction
        for tx in transactions:
            txid = tx['txid']
            tx_time = tx.get('time') if network_type in ['testnet', 'regtest'] else tx['status']['block_time']

            if network_type in ['testnet', 'regtest']:
                blockhash = tx.get('blockhash')  # Get the block hash from the transaction info
                # Fetch the transaction using getrawtransaction with verbosity = 2 to get full details including inputs
                tx_response = self.rpc_request('getrawtransaction', [txid, True, blockhash])

                if 'error' in tx_response and tx_response['error'] is not None:
                    print(f"Error fetching transaction {txid}: {tx_response['error']}")
                    continue
                tx = tx_response['result']

            # Iterate over outputs to check for OP_RETURN data
            rune_metadata = None
            for index, output in enumerate(tx['vout']):
                script_pub_key = output.get('scriptPubKey')
                if script_pub_key and script_pub_key.get('type') == 'nulldata':  # OP_RETURN for testnet/regtest
                    hex_data = script_pub_key['asm'].split(' ')[1]
                    rune_metadata = self.decode_rune_metadata(hex_data)
                elif network_type == 'mainnet' and output.get('scriptpubkey_type') == 'op_return':
                    hex_data = output['scriptpubkey_asm'].split(' ')[2]
                    rune_metadata = json.loads(bytes.fromhex(hex_data).decode('utf-8'))

                # If metadata found, process further
                if rune_metadata:
                    rune_originating_address = self.analyze_transaction_inputs(tx)
                    rune_metadata['originating_address'] = rune_originating_address

                    # Validate the originating address if on mainnet
                    runes_found[txid] = {
                        'rune_metadata': rune_metadata,
                        'tx_time': tx_time
                    }
                    self.lock_utxo(txid, index)  # Lock UTXO to prevent accidental spending
                
        # Step 4: Process and output Runes found
        if runes_found:
            runes_metadata_list = []

            # Sort by transaction time
            sorted_runes = sorted(runes_found.items(), key=lambda x: x[1]['tx_time'])

            for txid, data in sorted_runes:
                metadata = data['rune_metadata']
                expiration_date = ""
                issue_date = ""
                
                #If an expiration date is specified
                if metadata.get('expiration_date'):
                    expiration_date = datetime.strptime(metadata.get('expiration_date'), '%Y-%m-%d')

                #If not, default licence length is 1 year
                elif metadata.get('issued_date'):
                    issue_date = datetime.strptime(metadata.get('issued_date'), '%Y-%m-%d')
                    expiration_date = issue_date.replace(year=issue_date.year + 1)

                # Only include if not expired
                if expiration_date > datetime.now():
                    runes_metadata_list.append({
                        "Rune ID": metadata['rune_id'],
                        "Originating Address": metadata['originating_address'],
                        "Expiration Date": metadata.get('expiration_date'),
                        "Time of Issue": data["tx_time"],
                        "Transaction ID": txid
                    })

            return runes_metadata_list
        else:
            print("No valid Runes found in the wallet.")

    def analyze_transaction_inputs(self, tx_details):
        network_type = self.check_network_type()

        # If on mainnet, blockstream provides the originating address
        if network_type == 'mainnet':
            for vin in tx_details['vin']:
                # Check if 'prevout' exists
                if 'prevout' in vin:
                    originating_address = vin['prevout'].get('scriptpubkey_address', 'Unknown')
                    return originating_address
        
        # Otherwise, for testnet/regtest, manually analyze the inputs
        elif network_type == 'testnet' or network_type == 'regtest':
            outputs = tx_details['vout']
            inputs = tx_details['vin']

            originating_addresses = []
            total_input_amount = 0

            for input_tx in inputs:
                input_txid = input_tx['txid']
                input_vout = input_tx['vout']

                # Fetch the input transaction
                input_tx_response = self.rpc_request('getrawtransaction', [input_txid, True])
                if 'error' in input_tx_response and input_tx_response['error'] is not None:
                    print(f"Error fetching input transaction {input_txid}: {input_tx_response['error']}")
                    continue

                input_tx_details = input_tx_response['result']
                input_output = input_tx_details['vout'][input_vout]

                # Get the amount and scriptPubKey
                input_amount = input_output['value']
                script_pub_key = input_output['scriptPubKey']

                # Check for both 'address' and 'addresses' fields for compatibility
                if 'addresses' in script_pub_key:
                    originating_address = script_pub_key['addresses'][0]
                elif 'address' in script_pub_key:
                    originating_address = script_pub_key['address']
                else:
                    print(f"Unknown address format for input {input_txid}")
                    continue

                originating_addresses.append({'address': originating_address, 'amount': input_amount})
                total_input_amount += input_amount
                #print(f"Input from address {originating_address} with amount {input_amount} BTC")

            # Step 2: Analyze output to find potential change address
            total_output_amount = sum([output['value'] for output in outputs])
            possible_change_output = None

            if total_input_amount > total_output_amount:
                for output in outputs:
                    output_amount = output['value']
                    script_pub_key = output['scriptPubKey']
                    if 'addresses' in script_pub_key:
                        output_address = script_pub_key['addresses'][0]
                        if output_amount < total_input_amount / 2:
                            possible_change_output = output_address
                            break

            # Step 3: Determine likely originating address
            likely_originating_address = possible_change_output if possible_change_output else max(
                originating_addresses, key=lambda x: x['amount'], default={'address': 'Unknown'}
            )['address']

            return likely_originating_address


    def lock_utxo(self, txid, vout):
        # Get list of currently locked UTXOs
        locked_utxos_response = self.rpc_request('listlockunspent')
        
        if 'error' in locked_utxos_response and locked_utxos_response['error'] is not None:
            print(f"Error fetching locked UTXOs: {locked_utxos_response['error']}")
            return

        locked_utxos = locked_utxos_response['result']
        
        # Convert locked UTXOs to a set of tuples (txid, vout)
        locked_utxo_tuples = {(utxo['txid'], utxo['vout']) for utxo in locked_utxos}

        # Check if the UTXO is already locked
        utxo_to_lock = (txid, vout)
        if utxo_to_lock not in locked_utxo_tuples:
            # Lock the UTXO if it is not already locked
            self.rpc_request('lockunspent', [False, [{"txid": txid, "vout": vout}]])
            #print(f"Locked UTXO: {txid}, vout: {vout}")





if __name__ == "__main__":
    
#      # Initialize the RuneManager object
    rpc_user = 'your_rpc_username'
    rpc_password = 'your_rpc_password'

# #     #testnet
# #     #rpc_port = '18332'

# #     #regtest
#     # rpc_port = "18443"
#     # wallet_name = "legacy_wallet"



# #     #mainnet
    # rpc_port = '8332'
    # wallet_name = "wallet"

    # url = "http://localhost:"

# #     #response = self.rpc_request('createwallet', [wallet_name])

    # rune_manager = RuneManager(rpc_user, rpc_password, url+rpc_port, wallet_name)
#     response = rune_manager.rpc_request('loadwallet', [wallet_name])

# #     #regtest
# #    address = "bcrt1q4cf6tk7f8mf9d7m7a2yu4x2n22994yqfmjueny"
    
# #     #mainnet
    # address = "bc1qcc8cu06t2ukctrs57tznjdk3d3zm0ft229hjqr"
#     vaultaddress = "bc1qcc8cu06t2ukctrs57tznjdk3d3zm0ft229hjqr"

# #     # Mint a Rune
#     # regtest
    # rune_manager.mint_rune(address)

# #     #mainnet
# #     rune_manager.mint_rune(address, vaultaddress)

# #     #List Runes owned by the user
    # runes_list = rune_manager.read_runes_from_wallet()

    # if runes_list:
    #     for index, rune in enumerate(runes_list):
    #         print("Rune #", index)
    #         for key, value in rune.items():
    #             print(f"{key}: {value}")
    #         print()

    

#     #



#     # Get information about the wallet/address
#     #response = rpc_request('getwalletinfo')
#     # print(response)

#     # Generate a new address
#     # response = rpc_request('getnewaddress')
#     # new_address = response['result']
#     # print("New address:", new_address)


    
#     # response = rpc_request('getaddressinfo', [new_address])
#     # print(response)


#     #Get all addresses in the loaded wallet
#     #response = rpc_request('listaddressgroupings')
#     #addresses = response['result']
#     #print(f"All addresses: {addresses}")

#     # Get detailed information about the address
#     #response = rpc_request('getaddressinfo', [address])
#     #print(f"Address info: {response['result']}")




#     #Extract all addresses and retrieve their private keys
#     # addresses_and_keys = []

#     # Loop through all addresses and retrieve private keys
#     # for address_info in addresses[0]:  # The actual address is inside the inner list
#     #     address = address_info[0]  # Extract the address string
#     #     print(f"Retrieving private key for address: {address}")
        
#     #     # Use the dumpprivkey command to get the private key
#     #     private_key_response = rpc_request('dumpprivkey', [address])
        
#     #     # Check for any errors in the response
#     #     if private_key_response.get('error'):
#     #         print(f"Error: {private_key_response['error']}")
#     #     else:
#     #         private_key = private_key_response['result']
#     #         print(f"Private key for {address}: {private_key}")

#     # # Print out the addresses and their corresponding private keys
#     # for address, private_key in addresses_and_keys:
#     #     print(f"Address: {address}, Private Key: {private_key}")


#     #create wallet
#     #wallet_name = "testnet_wallet"
#     #

#     #load wallet
#     #wallet_name = "testnet_wallet"
#     #response = rpc_request('loadwallet', [wallet_name])
#     #print(response)
#     # response = rpc_request('listwallets')
#     # print("Loaded wallets:", response['result'])



#     # # Step 2: Retrieve the private key for the new address
#     # private_key_response = rpc_request('dumpprivkey', [new_address])
#     # private_key = private_key_response['result']
#     # print(f"Private key for {new_address}: {private_key}")

#     # Example of sending Bitcoin to a testnet address

#     # to_address = "your-recipient-testnet-address"
#     # amount = 0.01  # Amount in BTC

#     # response = rpc_request('sendtoaddress', [to_address, amount])
#     # print("Transaction ID:", response['result'])

#     # # Get wallet balance
#     # response = rpc_request('getbalance')
#     # print("Wallet balance:", response['result'])

