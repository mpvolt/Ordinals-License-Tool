# Bitcoin Licence Tool

This Project contains 

## Prerequisites

You need a locally running bitcoin node to run this tool: https://bitcoin.org/en/bitcoin-core/

## React Front-End

In main project directory, you can run:

 ```bash
 npm start
 ```

## Flask App

Inside the flask-app directory, run the following commands:

```bash
brew install python@3.11
python3.11 -m venv .venv
source .venv/bin/activate
pip install flask
pip install flask_cors
pip install requests
```

Once ready, run:
```bash
python app.py`
```

## Bitcoin-Proxy Server

Inside bitcoin-proxy, run:

```bash
 node server.js
 ```

### RPC Settings
Check http://localhost:3000/ to view the tool

Check the rpc settings by clicking the gear icon in the top right corner

![Gear Icon](assets/geariconpoint.png)

Apply the correct rpc settings and click Connect to Blockchain to test the connection

![Gear Icon](assets/rpcconnect.png)



