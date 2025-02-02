// src/WalletTransactions.js
import React, { useEffect, useState } from "react";
import { bitcoinRpcRequest, mintRune, readRunesFromUserWallet, fetchRunesMintedByUser, checkRpcCredentials } from "./bitcoinConnectApi";
import './WalletTransactions.css';
import { FaCog } from 'react-icons/fa';


const WalletTransactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [runes, setRunes] = useState([]);
  const [mintedRunes, setMintedRunes] = useState([]);
  const [activeTab, setActiveTab] = useState("transactions");
  
  // Loading states
  const [loadingTransactions, setLoadingTransactions] = useState(true);
  const [loadingRunes, setLoadingRunes] = useState(true);
  const [loadingMintedRunes, setLoadingMintedRunes] = useState(true);
  
  // Inputs for "Mint A Rune"
  const [expirationDate, setExpirationDate] = useState("");
  const [licenceID, setLicenceID] = useState("Generated ID");
  const [destinationAddress, setDestinationAddress] = useState("");
  const [revokeAddress, setRevokeAddress] = useState("")
  const [mintTxn, setMintTxn] = useState("")

  //Extra elements
  const [isLoading, setIsLoading] = useState(false);
  const [showPopup, setShowPopup] = useState(false);
  const [message, setMessage] = useState('');
  const [linkMessage, setLinkMessage] = useState('');
  const [isSuccess, setIsSuccess] = useState(false); // For styling the message


  const [rpcUser, setRpcUser] = useState(localStorage.getItem('rpcUser') || '');
  const [rpcPassword, setRpcPassword] = useState(localStorage.getItem('rpcPassword') || '');
  const [url, setUrl] = useState(localStorage.getItem('url') || '');
  const [port, setPort] = useState(localStorage.getItem('port') || '');
  const [walletDirectory, setWalletDirectory] = useState(localStorage.getItem('walletDirectory') || '');
  const [walletName, setWalletName] = useState(localStorage.getItem('walletName') || '');

  const [rpcString, setRpcString] = useState('')

  const exampleRPCString = 'http://your_rpc_username:your_rpc_password@localhost:8332/wallet/wallet'

  const togglePopup = () => {
    setShowPopup(!showPopup);
  };

  const saveSettings = () => {
    localStorage.setItem('rpcUser', rpcUser);
    localStorage.setItem('rpcPassword', rpcPassword);
    localStorage.setItem('url', url);
    localStorage.setItem('port', port);
    localStorage.setItem('walletDirectory', walletDirectory);
    localStorage.setItem('walletName', walletName);
    setLinkMessage("RPC connection successful! Settings Have Been Saved");
    setIsSuccess(true);
  };

  useEffect(() => {
    (async () => {

      // Load saved settings on component mount
      const savedRpcUser = localStorage.getItem('rpcUser');
      const savedRpcPassword = localStorage.getItem('rpcPassword');
      const savedUrl = localStorage.getItem('url');
      const savedPort = localStorage.getItem('port');
      const savedWalletDirectory = localStorage.getItem('walletDirectory');
      const savedWalletName = localStorage.getItem('walletName');

      if (savedRpcUser) setRpcUser(savedRpcUser);
      if (savedRpcPassword) setRpcPassword(savedRpcPassword);
      if (savedUrl) setUrl(savedUrl);
      if (savedPort) setPort(savedPort);
      if (savedWalletDirectory) setWalletDirectory(savedWalletDirectory);
      if (savedWalletName) setWalletName(savedWalletName);

      await callBitcoinRpc()

    })();
  }, []);


  const today = new Date().toISOString().split('T')[0];

  const fetchData = async () => {
    try {
      // Fetch transactions
      setLoadingTransactions(true);
      const txs = await bitcoinRpcRequest("listtransactions", ["*", 10, 0]);
      if (txs) 
        setTransactions(txs);
      setLoadingTransactions(false);

      // Fetch user runes
      setLoadingRunes(true);
      const userRunes = await readRunesFromUserWallet();
      if (userRunes) 
        setRunes(userRunes);

      setLoadingRunes(false);

      // Fetch minted runes
      setLoadingMintedRunes(true);
      const runesMinted = await fetchRunesMintedByUser();
      if (runesMinted)
        setMintedRunes(runesMinted);
      
      setLoadingMintedRunes(false);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };


  const mintNewRune = async () => {
    if (!destinationAddress || !expirationDate) {
      showErrorPopup();
      return;
    }

    setIsLoading(true); // Show the loading icon
    setMessage(''); // Clear any previous message

    const mintTxn = await mintRune({'to_address': destinationAddress, 'expiration_date': expirationDate}, rpcString)
    console.log(mintTxn)
    if (mintTxn) {
      setMintTxn(mintTxn); // Save the TXID
      setMessage(`Rune minted with TXID: ${mintTxn}`); // Display the TXID in the message
    }
    else{
      setMessage("Error revoking licence. Please check the connection, and make sure have enough funds");
    }
    setIsLoading(false); // Hide the loading icon

  }

  const revokeLicence = async () => {
    if (!revokeAddress) {
      showErrorPopup();
      return;
    }
  
    const today = new Date().toISOString().split('T')[0]; // Get today's date in YYYY-MM-DD format
  
    setIsLoading(true); // Show the loading icon
    setMessage(''); // Clear any previous message
  
    const revokeTxn = await mintRune({ 'to_address': revokeAddress, 'expiration_date': today }, rpcString);
    console.log(revokeTxn);
    if (revokeTxn) {
      setMintTxn(revokeTxn); // Save the TXID
      setMessage(`Licence revoked with TXID: ${revokeTxn}\nThey will have access until EOD`); // Display the TXID in the message
    } else {
      setMessage("Error revoking licence. Please check the connection, and make sure have enough funds");
    }
  
    setIsLoading(false); // Hide the loading icon
  };
  

  const callBitcoinRpc = async() => {
    try {
      setRpcString(`http://${rpcUser}:${rpcPassword}@${url}:${port}/${walletDirectory}/${walletName}`);
      const confirmation = await checkRpcCredentials(`http://${rpcUser}:${rpcPassword}@${url}:${port}/${walletDirectory}/${walletName}`);
      if (confirmation) {
        console.log(confirmation);
        setIsSuccess(true);
        saveSettings()
        await fetchData()
        return true;
      } else {
        setLinkMessage("RPC connection failed. Please check your settings.");
        setIsSuccess(false);
        return false;
      }
    } catch (error) {
      console.error("Error connecting to Bitcoin RPC:", error.message);
      setLinkMessage("An unexpected error occurred. Please try again.");
      setIsSuccess(false);
      return false;
    }
  }

  const showErrorPopup = () => {
    alert('Error: Please ensure Destination Address, and Expiration Date are set.');
  };


  const handlePresetChange = (e) => {
    const preset = e.target.value;
    const now = new Date();
    let calculatedDate;

    switch (preset) {
      case "1 day":
        calculatedDate = new Date(now.setDate(now.getDate() + 1));
        break;
      case "1 week":
        calculatedDate = new Date(now.setDate(now.getDate() + 7));
        break;
      case "1 month":
        calculatedDate = new Date(now.setMonth(now.getMonth() + 1));
        break;
      case "6 months":
        calculatedDate = new Date(now.setMonth(now.getMonth() + 6));
        break;
      case "1 year":
        calculatedDate = new Date(now.setFullYear(now.getFullYear() + 1));
        break;
      default:
        calculatedDate = "";
    }

    if (calculatedDate) {
      const formattedDate = calculatedDate.toISOString().split("T")[0];
      setExpirationDate(formattedDate);
    }
  };

  const getFieldValue = (data, key1, key2) => {
    return data[key1] || data[key2] || 'N/A'; // Check for the first key, then the second, or return 'N/A' if none exists
  };

  return (
    <div className="wallet-container">
      <h1>Asset Reality Licence Tool</h1>

      {/* Gear Icon */}
      <div className="gear-icon" onClick={togglePopup}>
        <FaCog size={24} />
      </div>

      {/* Popup */}
      {showPopup && (
        <div className="popup-overlay" onClick={togglePopup}>
          <div className="popup-content" onClick={(e) => e.stopPropagation()}>
            <h2>Bitcoin RPC Settings</h2>
            <strong>Check RPC Connection: </strong>
            <button className='test-connection' onClick={callBitcoinRpc} >Connect To Blockchain</button>
            {linkMessage && (
              <p className={`message ${isSuccess ? "success" : "error"}`}>{linkMessage}</p>
            )}
            <div className="form-group">
              <label>RPC User</label>
              <input
                type="text"
                value={rpcUser}
                onChange={(e) => setRpcUser(e.target.value)}
                placeholder="Example: my_rpc_username"
              />
            </div>
            <div className="form-group">
              <label>RPC Password</label>
              <input
                type="text"
                value={rpcPassword}
                onChange={(e) => setRpcPassword(e.target.value)}
                placeholder="Example: my_rpc_password"
              />
            </div>
            <div className="form-group">
              <label>URL</label>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Example: localhost"
              />
            </div>
            <div className="form-group">
              <label>Port</label>
              <input
                type="text"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                placeholder="Example: 8332"
              />
            </div>
            <div className="form-group">
              <label>Wallet Directory Name</label>
              <input
                type="text"
                value={walletDirectory}
                onChange={(e) => setWalletDirectory(e.target.value)}
                placeholder="Example: wallets"
              />
            </div>
            <div className="form-group">
              <label>Wallet Name</label>
              <input
                type="text"
                value={walletName}
                onChange={(e) => setWalletName(e.target.value)}
                placeholder="Example: wallet"
              />
            </div>
            <div className="rpc-string">
              <strong>Your RPC String:</strong>
              <p>{rpcString}</p>
              <strong>Example:</strong>
              <p>{exampleRPCString}</p>
            </div>
            <button onClick={togglePopup}>Close</button>
          </div>
        </div>
      )}
      
      <div className="tabs">
        <button onClick={() => setActiveTab("transactions")} className={activeTab === "transactions" ? "active" : ""}>
          Sent Transactions
        </button>
        <button onClick={() => setActiveTab("runes")} className={activeTab === "runes" ? "active" : ""}>
          Runes Owned
        </button>
        <button onClick={() => setActiveTab("mintedRunes")} className={activeTab === "mintedRunes" ? "active" : ""}>
          Runes Minted
        </button>
        <button onClick={() => setActiveTab("mintARune")} className={activeTab === "mintARune" ? "active" : ""}>
          Mint a Rune
        </button>
      </div>
      
      <div className="content">
        {activeTab === "transactions" && (
          <div>
            <h2>Sent Transactions</h2>
            {loadingTransactions ? (
              <div className="spinner"></div>
            ) : transactions.length === 0 ? (
              <p>No transactions found.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Transaction ID</th>
                    <th>Amount</th>
                    <th>Confirmations</th>
                    <th>Address</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) =>
                    tx.category === "send" ? (
                      <tr>
                        <td>
                          <a
                            href={`https://www.blockchain.com/explorer/transactions/btc/${tx.txid}`}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                          {tx.txid}
                          </a>
                        </td>
                        <td>{tx.amount}</td>
                        <td>{tx.confirmations}</td>
                        <td>{tx.address}</td>
                      </tr>
                    ) : null
                  )}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === "runes" && (
          <div>
            <h2>Runes Owned by User</h2>
            {loadingRunes ? (
              <div className="spinner"></div>
            ) : runes.length === 0 ? (
              <p>No Runes found.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Expiration Date</th>
                    <th>Rune ID</th>
                    <th>Date of Issue</th>
                    <th>Transaction ID</th>
                    <th>Originating Address</th>
                  </tr>
                </thead>
                <tbody>
                  {runes.map((rune) => (
                    <tr>
                      <td>{rune["Expiration Date"]}</td>
                      <td>{rune["Rune ID"]}</td>
                      <td>{new Date(rune["Time of Issue"] * 1000).toLocaleString()}</td> 
                      <td>
                        <a
                          href={`https://www.blockchain.com/explorer/transactions/btc/${rune['Transaction ID']}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                        {rune['Transaction ID']}
                        </a>
                      </td>
                      <td>{rune["Originating Address"]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === "mintedRunes" && (
          <div>
            <h2>Runes Minted by User</h2>
            {loadingMintedRunes ? (
              <div className="spinner"></div>
            ) : mintedRunes.length === 0 ? (
              <p>No Runes found.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Rune ID</th>
                    <th>Date of Issue</th>
                    <th>Expiration Date</th>
                    <th>Transaction ID</th>
                    <th>Recipient</th>
                  </tr>
                </thead>
                <tbody>
                  {mintedRunes.map((mintedRune, index) => (
                    <tr key={index}>
                      <td>{getFieldValue(mintedRune.rune_metadata, 'Rune ID', 'rune_id')}</td>
                      <td>{new Date(mintedRune["block_time"] * 1000).toLocaleString()}</td> 
                      <td>{getFieldValue(mintedRune.rune_metadata, 'Expiration Date', 'expiration_date')}</td>
                      <td>
                        <a
                          href={`https://www.blockchain.com/explorer/transactions/btc/${mintedRune.txid}`}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                        {mintedRune.txid}
                        </a>
                      </td>
                      <td>{mintedRune.recipient}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === "mintARune" && (
          <div>
            <h2>Mint a Licence</h2>
            <div className="date-selectors">
              <div className="form-group">
                <label>Select Expiration Date:</label>
                <input
                  id="expirationDate"
                  type="date"
                  value={expirationDate}
                  onChange={(e) => setExpirationDate(e.target.value)}
                  min={today} // Set the minimum date to today
                />
              </div>
              <div className="form-group">
                <label>Or Select Length of Licence:</label>
                <select onChange={handlePresetChange}>
                  <option value="">Select preset</option>
                  <option value="1 day">1 Day</option>
                  <option value="1 week">1 Week</option>
                  <option value="1 month">1 Month</option>
                  <option value="6 months">6 Months</option>
                  <option value="1 year">1 Year</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>Licence Recipient/Destination Address:</label>
              <input type="text" value={destinationAddress} onChange={(e) => setDestinationAddress(e.target.value)}/>
            </div>
            <div className="form-group">
              <button className="send" onClick={mintNewRune} disabled={isLoading}>
                {isLoading ? 'Processing...' : 'Mint Licence'}
              </button>

              {/* Loading Icon */}
              {isLoading && <div className="spinner">Loading...</div>}

              {/* Success or Error Message */}
              <div className="message">
                {message && (
                  <div 
                    className={`message ${message.toLowerCase().includes('error') ? 'message-error' : 'message-success'}`}
                  >
                    {message}
                  </div>
                )}
              </div>
            </div>
            <h1>Or</h1>
            <h2>Revoke a licence </h2>
            <div className="form-group">
              <label>Licence Recipient/Destination Address:</label>
              <input type="text" value={revokeAddress} onChange={(e) => setRevokeAddress(e.target.value)}/>
            </div>
            <div className="form-group">
              <button className="send" onClick={revokeLicence} disabled={isLoading}>
                {isLoading ? 'Processing...' : 'Revoke Licence'}
              </button>       
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WalletTransactions;
