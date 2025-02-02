// src/bitcoinApi.js
import axios from "axios";

// Global variables
let rpcUser = "";
let rpcPassword = "";
let rpcUrl = "";

// Function to parse RPC string and set global variables
const parseRpcString = (rpcString) => {
  const regex = /http:\/\/(.*?):(.*?)@(.*?):(.*?)\/(.*)\/(.*)/;
  const match = rpcString.match(regex);

  if (!match) {
    throw new Error("Invalid RPC string format");
  }

  // Destructure matched groups
  const [ , parsedRpcUser, parsedRpcPassword, url, port, walletDirectory, walletName ] = match;

  // Set global variables
  rpcUser = parsedRpcUser;
  rpcPassword = parsedRpcPassword;
  rpcUrl = `http://${url}:${port}/${walletDirectory}/${walletName}`;

  // Return parsed values (optional)
  return {
    rpcUser,
    rpcPassword,
    rpcUrl,
  };
};


export const checkRpcCredentials = async (connectionString) => {
  
  try {
    // Send the request to the server
    const response = await axios.post("http://127.0.0.1:3001/check_rpc_credentials", parseRpcString(connectionString));

    // Handle and return the response
    if (response.data && response.data.success) {
      console.log("Valid credentials:", response.data);
      return response.data;
    } else {
      console.error("Invalid credentials or error:", response.data.message);
      return null;
    }
  } catch (error) {
    console.error("Bitcoin RPC request failed:", error.message);
    return null;
  }
};

export const bitcoinRpcRequest = async (method, params = []) => {
  const data = {
    jsonrpc: "1.0",
    id: "wallet-viewer",
    method,
    params,
    rpcUser,
    rpcPassword,
    rpcUrl,
  };

  try {
    const response = await axios.post("http://127.0.0.1:3001/bitcoin-rpc", data);

    if (response.data && response.data.result !== undefined) {
      return response.data.result;
    } else {
      console.error("No result in Bitcoin RPC response", response.data);
      return null;
    }
  } catch (error) {
    console.error("Bitcoin RPC request failed", error.message);
    return null;
  }
};

export const mintRune = async (data, connectionString) => {
  try {
    // Assume parseRpcString splits connectionString into rpcUser, rpcPassword, rpcUrl
    const { rpcUser, rpcPassword, rpcUrl } = parseRpcString(connectionString);

    const requestData = {
      ...data, // Include to_address and expiration_date
      rpcUser,
      rpcPassword,
      rpcUrl,
    };

    console.log("Request Data:", requestData);

    const response = await axios.post(
      "http://127.0.0.1:5000/mint_rune",
      requestData, // Send as JSON body
      {
        headers: {
          "Content-Type": "application/json", // Ensure JSON content type
        },
      }
    );
    return response.data.txid;
  } catch (error) {
    console.error("Error calling Python function:", error);
    return null;
  }
};

export const readRunesFromUserWallet = async () => {
  try {
    
    const response = await axios.get("http://127.0.0.1:5000/read_runes_from_user_wallet", {
      params: { 'rpcUser': rpcUser, 'rpcPassword': rpcPassword, 'rpcUrl':rpcUrl }, // Pass as query parameters
      headers: {
        "Content-Type": "application/json", // Optional but recommended for consistency
      },
    });    
    console.log(response);
    return response.data.runes_list;
  } catch (error) {
    console.error("Error calling Python function:", error);
    return null;
  }
};

export const fetchRunesMintedByUser = async () => {
  try {
    
    const response = await axios.get("http://127.0.0.1:5000/read_runes_minted_by_user", {
      params: { 'rpcUser': rpcUser, 'rpcPassword': rpcPassword, 'rpcUrl':rpcUrl }, 
      headers: {
        "Content-Type": "application/json", // Optional but recommended for consistency
      },
    });
    console.log(response);
    return response.data.runes_minted;
  } catch (error) {
    console.error("Error calling Python function:", error);
    return null;
  }
};

