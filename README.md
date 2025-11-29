# 🐋 Whaleer.com - Profit Sharing Demo

> **A demonstration of how Whaleer.com's profit-sharing system works using Stellar blockchain and Soroban smart contracts**

This project demonstrates the commission flow and profit-sharing mechanism that powers [Whaleer.com](https://whaleer.com) - a platform where expert traders ("whales") share their trading signals with followers.

---

## 🎯 What is Whaleer.com?

Whaleer.com connects **expert traders (Developers)** with **followers (Users)** through a transparent, blockchain-based profit-sharing system:

- **Developers** create trading bots/signals and set their commission rate
- **Users** follow these bots and pay commission only when profits are made
- **Platform** takes a small cut (10% of developer's commission)
- **Smart Contract** handles all commission distributions automatically

---

## 📊 Commission Flow Diagram

```
                                    PROFIT MADE ($100)
                                          │
                                          ▼
                            ┌─────────────────────────────┐
                            │   Developer sets rate: 10%  │
                            │   Total commission: $10     │
                            └─────────────────────────────┘
                                          │
                          ┌───────────────┴───────────────┐
                          ▼                               ▼
                  ┌──────────────┐                ┌──────────────┐
                  │  Developer   │                │   Platform   │
                  │    (90%)     │                │    (10%)     │
                  │     $9       │                │     $1       │
                  └──────────────┘                └──────────────┘
```

### Key Points:
- **User pays**: Only from profits, never from principal
- **Developer gets**: 90% of the commission they set
- **Platform gets**: 10% of developer's commission (not user's money)
- **Smart Contract**: Handles distribution trustlessly

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER'S BROWSER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     Next.js Frontend (React)                         │    │
│  │  • Wallet Connection (Freighter)                                     │    │
│  │  • Bot Selection & Deposit                                           │    │
│  │  • Daily Simulation & Receipts                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ REST API
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND SERVER                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Python Flask API (Port 5328)                      │    │
│  │  • Transaction Building                                              │    │
│  │  • Real-time XLM Price (CoinGecko)                                   │    │
│  │  • Profit Simulation                                                 │    │
│  │  • Commission Calculation                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ Stellar SDK
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STELLAR BLOCKCHAIN (Testnet)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Soroban Smart Contract                            │    │
│  │  • init_vault: Create user vault with commission rates               │    │
│  │  • deposit: Lock XLM as commission reserve                           │    │
│  │  • settle_profit: Distribute commission on profit                    │    │
│  │  • withdraw: Return remaining balance to user                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Contract ID: CBEZLTP6IW3KETVKHHQIZP6MV4N5ROD3O2YMXE3WPDBHWYO53UBDJDFI      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 💰 How It Works (Step by Step)

### 1️⃣ User Deposits Commission Reserve
```
User ──────────────────────────────────────────────► Smart Contract
         Deposit 100 XLM (commission reserve)
         
• This is NOT an investment, it's a reserve for future commissions
• User keeps trading with their own capital elsewhere
• XLM is locked in the smart contract vault
```

### 2️⃣ Daily Trading Simulation
```
Bot generates trading signals
         │
         ▼
┌─────────────────────────────────────┐
│ Day 1: +4.2% profit ($4.20)        │──► Commission: 0.42 XLM
│ Day 2: -1.5% loss ($1.50)          │──► No commission (loss)
│ Day 3: +2.8% profit ($2.80)        │──► Commission: 0.28 XLM
│ Day 4: +5.1% profit ($5.10)        │──► Commission: 0.51 XLM
│ ...                                 │
└─────────────────────────────────────┘

• Commission only charged on profits
• High-Water Mark prevents double-charging
• Real-time XLM/USD price from CoinGecko
```

### 3️⃣ Commission Distribution (On Each Profit)
```
                    Profit: $5.00
                         │
                         ▼
              Total Commission: 10%
                    = $0.50
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
      Developer: 90%            Platform: 10%
        = $0.45                   = $0.05
        (≈1.76 XLM)              (≈0.20 XLM)
            │                         │
            ▼                         ▼
    ┌───────────────┐        ┌───────────────┐
    │ Developer     │        │ Platform      │
    │ Wallet        │        │ Wallet        │
    └───────────────┘        └───────────────┘
```

### 4️⃣ User Withdraws
```
Smart Contract ──────────────────────────────────► User
                  Remaining balance (e.g., 87 XLM)
                  
• User can withdraw anytime
• Only commission for realized profits is deducted
• No lock-up period
```

---

## 🔧 Technical Details

### Smart Contract Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `init_vault` | Create user's vault | bot_id, user_id, addresses, rates |
| `deposit` | Lock XLM in vault | bot_id, user_id, amount |
| `settle_profit` | Distribute commission | bot_id, user_id, profit_amount |
| `withdraw` | Return remaining XLM | bot_id, user_id |

### Commission Calculation (BPS = Basis Points)

```rust
// In Smart Contract
let total_commission = profit_amount * profit_share_bps / 10000;
let platform_fee = total_commission * platform_cut_bps / 10000;
let developer_fee = total_commission - platform_fee;
```

Example with 10% developer rate:
- `profit_share_bps = 1000` (10%)
- `platform_cut_bps = 1000` (10% of commission)
- On 100 XLM profit:
  - Total commission: 10 XLM
  - Platform: 1 XLM
  - Developer: 9 XLM

---

## 🚀 Running the Demo

### Prerequisites
- Node.js v18+
- Python 3.9+
- [Freighter Wallet](https://freighter.app/) browser extension

### Installation

```bash
# Clone the repository
git clone https://github.com/Apollous1592/Stellar-Hackathon-Project-Whaleer.com.git
cd "Stellar Alternative"

# Install frontend
cd frontend
npm install

# Install backend
cd ../api
pip install -r requirements.txt
```

### Running

**Terminal 1 - Backend:**
```bash
cd api
python index.py
# Runs on http://127.0.0.1:5328
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
```

### Using the Demo

1. **Connect Wallet**: Click "Connect Freighter" (use Stellar Testnet)
2. **Select Bot**: Choose a trading bot to follow
3. **Deposit**: Deposit XLM as commission reserve
4. **Simulate**: Click "Simulate Day" to see daily P&L
5. **Watch**: See commission distributed in real-time
6. **Withdraw**: Take back remaining balance anytime

---

## 📁 Project Structure

```
Stellar Alternative/
├── frontend/                 # Next.js React Application
│   ├── app/
│   │   ├── page.tsx         # Main UI component
│   │   ├── layout.tsx       # App layout
│   │   └── globals.css      # Styles
│   ├── package.json
│   └── next.config.js       # API proxy config
│
├── api/                      # Python Flask Backend
│   ├── index.py             # Main API + Stellar integration
│   ├── requirements.txt     # Python dependencies
│   └── vault_keys.json      # Testnet keys (gitignored)
│
├── stellar-rs/              # Soroban Smart Contract (Rust)
│   ├── src/lib.rs          # Contract logic
│   └── Cargo.toml          # Rust dependencies
│
└── README.md
```

---

## 🔐 Security Notes

⚠️ **This is a TESTNET demo** - No real funds are involved

- Uses Stellar Testnet (fake XLM)
- Smart contract is for demonstration only
- In production, Whaleer.com uses additional security measures

---

## 🌐 Links

- **Whaleer.com**: [https://whaleer.com](https://whaleer.com)
- **Stellar**: [https://stellar.org](https://stellar.org)
- **Soroban Docs**: [https://soroban.stellar.org](https://soroban.stellar.org)
- **Freighter Wallet**: [https://freighter.app](https://freighter.app)

---

## 📝 License

MIT License - Built for Stellar Hackathon 2025

---

<p align="center">
  <b>🐋 Whaleer.com - Follow the Whales, Share the Profits 🐋</b>
</p>
