# 🐋 Profit Sharing App

A profit-sharing web application that uses a Next.js frontend and Python backend, integrating with the Stellar blockchain (testnet) for handling commission deposits.

## Overview

This application demonstrates a profit-sharing mechanism where "whale" traders (experts) trade on behalf of users. The user's commission deposit is held on Stellar as a guarantee for profit-sharing. The whale takes a percentage of profits as commission.

### Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌──────────────────┐
│   Next.js       │  API    │   Python/Flask  │ Stellar │   Stellar        │
│   Frontend      │ ──────► │   Backend       │ ──────► │   Testnet        │
│   (Port 3000)   │         │   (Port 5328)   │   SDK   │   Blockchain     │
└─────────────────┘         └─────────────────┘         └──────────────────┘
```

- **Frontend (Next.js)**: Interactive UI for viewing bots, making deposits, and managing commissions
- **Backend (Python/Flask)**: REST API handling Stellar blockchain operations
- **Stellar Testnet**: Blockchain for secure commission deposits and settlements

## Features

- 🤖 **Bot Listing**: View available trading bots with their strategies and performance
- 💰 **Commission Deposits**: Deposit XLM to a bot's vault to start following
- 📈 **Profit Simulation**: Simulate trading profits (for demo purposes)
- 🔄 **Settlement**: Pay commission from deposit when profits are realized
- 💸 **Withdrawal**: Withdraw remaining deposit at any time
- 🔑 **Account Generation**: Generate Stellar testnet accounts with free XLM

## Prerequisites

- **Node.js** v18 or higher
- **Python** 3.9 or higher
- **npm** or **yarn**

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd "Stellar Alternative"
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Install Backend Dependencies

```bash
cd api
pip install -r requirements.txt
```

## Running the Application

You need to run both the frontend and backend simultaneously.

### Terminal 1: Start the Python Backend

```bash
cd api
python index.py
```

The backend will:
- Initialize Stellar accounts for each trading bot
- Fund vault accounts via Stellar Friendbot
- Start listening on `http://127.0.0.1:5328`

### Terminal 2: Start the Next.js Frontend

```bash
cd frontend
npm run dev
```

The frontend will start at `http://localhost:3000`

### Access the Application

Open your browser and navigate to: **http://localhost:3000**

## Usage Guide

### 1. Generate a Test Account

Click **"Generate New Test Account"** to create a Stellar testnet account funded with 10,000 XLM.

> ⚠️ **Save your secret key!** It won't be shown again. This is for testnet only.

### 2. Deposit Commission

1. Choose a trading bot from the list
2. Click **"Deposit Commission"**
3. Confirm the deposit amount (default: required deposit)
4. The transaction will be processed on Stellar testnet

### 3. Simulate Trading

Once you have an active deposit:
1. Use the **"+5% Profit"**, **"+10% Profit"**, or **"-3% Loss"** buttons
2. Watch your simulated balance and profit change

### 4. Settle Commission

Click **"Settle"** to pay the whale their commission from your deposit:
- Commission = Profit × Commission Rate (e.g., 10%)
- The commission is transferred on Stellar blockchain

### 5. Withdraw Remaining Deposit

Click **"Withdraw"** to:
- Receive remaining deposit back to your Stellar account
- End your engagement with that bot

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bots` | GET | List available trading bots |
| `/generate-account` | POST | Generate and fund a new testnet account |
| `/deposit` | POST | Deposit commission to a bot's vault |
| `/status` | GET | Get user's status and active bots |
| `/simulate-profit` | POST | Simulate profit/loss for testing |
| `/settle` | POST | Settle commission payment |
| `/withdraw` | POST | Withdraw remaining deposit |
| `/health` | GET | Health check |

## Project Structure

```
Stellar Alternative/
├── frontend/                 # Next.js application
│   ├── app/
│   │   ├── globals.css      # Global styles
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Main page component
│   ├── next.config.js       # API proxy configuration
│   ├── package.json
│   └── tsconfig.json
│
├── api/                      # Python Flask backend
│   ├── index.py             # Main API server
│   └── requirements.txt     # Python dependencies
│
└── README.md
```

## How Commission Works

1. **Deposit**: User deposits XLM (e.g., $50 worth) to the bot's vault
2. **Trading**: Whale trades on user's behalf (simulated in this demo)
3. **Profit**: If trades are profitable, commission is calculated
4. **Settlement**: Commission (e.g., 10% of profits) is paid to whale
5. **Withdrawal**: User can withdraw remaining deposit anytime

### Example Scenario

1. Alice deposits 50 XLM to Bot Alpha
2. Simulated trading generates $250 profit (5% of $5000)
3. Commission due: $25 (10% of $250)
4. Settlement transfers 25 XLM from vault to whale
5. Remaining deposit: 25 XLM
6. Alice can withdraw 25 XLM or continue trading

## Security Notes

⚠️ **TESTNET ONLY**: This application uses Stellar testnet. No real funds are involved.

- Never use testnet keys on mainnet
- Secret keys are stored in browser localStorage (development only)
- In production, use proper key management and authentication

## Stellar Testnet Resources

- [Stellar Laboratory](https://laboratory.stellar.org/) - Test transactions and accounts
- [Friendbot](https://friendbot.stellar.org/) - Fund testnet accounts
- [Horizon Testnet](https://horizon-testnet.stellar.org/) - API explorer

## Troubleshooting

### Backend won't start
- Ensure Python 3.9+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check if port 5328 is available

### Frontend API calls fail
- Ensure backend is running on port 5328
- Check `next.config.js` has correct rewrite rules
- Look for CORS errors in browser console

### Stellar transactions fail
- Ensure account is funded via Friendbot
- Check if account has enough XLM for fees
- Verify you're using testnet secret keys

## License

MIT License - feel free to use and modify for your own projects.
