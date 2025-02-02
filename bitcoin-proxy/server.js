// server.js
const express = require("express");
const axios = require("axios");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());
app.use(bodyParser.json());

// Configuration object for RPC credentials
const RPC_CONFIG = {
  user: "",
  password: "",
  url: "",
};

// Setter function to update RPC credentials
const setRpcCredentials = (rpcUser, rpcPassword, rpcUrl) => {
  RPC_CONFIG.user = rpcUser;
  RPC_CONFIG.password = rpcPassword;
  RPC_CONFIG.url = rpcUrl;
};



// Dynamic RPC credentials check function
const checkRpcCredentials = async ({ rpcUser, rpcPassword, rpcUrl }) => {
  try {
    // Define the RPC payload for getblockchaininfo
    const payload = {
      jsonrpc: "1.0",
      id: "checkcredentials",
      method: "getblockchaininfo",
      params: [],
    };

    // Make the RPC call
    const response = await axios.post(rpcUrl, payload, {
      auth: {
        username: rpcUser,
        password: rpcPassword,
      },
      headers: {
        "Content-Type": "application/json",
      },
    });

    setRpcCredentials(rpcUser, rpcPassword, rpcUrl);

    // Return parsed response
    return {
      success: true,
      message: "RPC credentials are valid",
      data: response.data.result,
    };
  } catch (error) {
    console.error("RPC error:", error.message);

    // Handle common errors
    if (error.response && error.response.status === 401) {
      return {
        success: false,
        message: "Invalid RPC credentials",
      };
    } else if (error.response && error.response.status === 403) {
      return {
        success: false,
        message: "Access denied",
      };
    } else {
      return {
        success: false,
        message: "Error connecting to Bitcoin server",
      };
    }
  }
};

// Express endpoint to dynamically validate RPC credentials
app.post("/check_rpc_credentials", async (req, res) => {
  const { rpcUser, rpcPassword, rpcUrl } = req.body;

  if (!rpcUser || !rpcPassword || !rpcUrl) {
    return res.status(400).json({
      success: false,
      message: "Missing rpcUser, rpcPassword, or rpcUrl",
    });
  }

  const result = await checkRpcCredentials({ rpcUser, rpcPassword, rpcUrl });
  res.status(result.success ? 200 : 500).json(result);
});


app.post("/bitcoin-rpc", async (req, res) => {
  const { rpcUser, rpcPassword, rpcUrl, ...rpcPayload } = req.body;

  if (!rpcUser || !rpcPassword || !rpcUrl) {
    return res.status(400).json({
      success: false,
      message: "Missing rpcUser, rpcPassword, or rpcUrl",
    });
  }

  try {
    const response = await axios.post(rpcUrl, rpcPayload, {
      auth: {
        username: rpcUser,
        password: rpcPassword,
      },
      headers: {
        "Content-Type": "application/json",
      },
    });
    res.json(response.data);
  } catch (error) {
    console.error("Proxy error:", error.message);
    res.status(500).send("Error connecting to Bitcoin server");
  }
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`Bitcoin proxy server running on http://localhost:${PORT}`);
});

