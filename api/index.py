"""
Profit Sharing App - Python Backend
Flask API server with Stellar testnet integration
Commission-based access with separate trading simulation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from stellar_sdk import Keypair, Server, TransactionBuilder, Network, Asset
from stellar_sdk.exceptions import NotFoundError, BadRequestError
import requests
import json
import os
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Stellar Testnet Configuration
HORIZON_URL = "https://horizon-testnet.stellar.org"
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE
FRIENDBOT_URL = "https://friendbot.stellar.org"

# Initialize Stellar server
server = Server(horizon_url=HORIZON_URL)

# File to persist vault keys
VAULT_KEYS_FILE = "vault_keys.json"

# In-memory storage
user_sessions = {}

# Pre-configured trading bots
TRADING_BOTS = [
    {
        "id": "bot-alpha",
        "name": "Bot Alpha",
        "strategy": "Trend Following - EMA crossovers",
        "commission_rate": 10,  # 10% of profits
        "min_commission_deposit": 10,  # Minimum XLM to deposit
        "deposit_address": "",
        "whale_address": "",
        "vault_secret": "",
        "whale_secret": "",
    },
    {
        "id": "bot-beta",
        "name": "Bot Beta", 
        "strategy": "Arbitrage - Cross-exchange",
        "commission_rate": 12,
        "min_commission_deposit": 5,
        "deposit_address": "",
        "whale_address": "",
        "vault_secret": "",
        "whale_secret": "",
    },
    {
        "id": "bot-gamma",
        "name": "Bot Gamma",
        "strategy": "DCA - Smart timing",
        "commission_rate": 8,
        "min_commission_deposit": 5,
        "deposit_address": "",
        "whale_address": "",
        "vault_secret": "",
        "whale_secret": "",
    },
]

# Starting simulation balance for each user
STARTING_SIMULATION_BALANCE = 1000.0  # $1000 virtual money

def save_vault_keys():
    """Save vault keys to file for persistence"""
    keys_data = {}
    for bot in TRADING_BOTS:
        keys_data[bot['id']] = {
            "deposit_address": bot['deposit_address'],
            "whale_address": bot['whale_address'],
            "vault_secret": bot['vault_secret'],
            "whale_secret": bot['whale_secret']
        }
    
    with open(VAULT_KEYS_FILE, 'w') as f:
        json.dump(keys_data, f, indent=2)
    print(f"[VAULT] Keys saved to {VAULT_KEYS_FILE}")

def load_vault_keys():
    """Load vault keys from file if exists"""
    if not os.path.exists(VAULT_KEYS_FILE):
        return False
    
    try:
        with open(VAULT_KEYS_FILE, 'r') as f:
            keys_data = json.load(f)
        
        for bot in TRADING_BOTS:
            if bot['id'] in keys_data:
                bot['deposit_address'] = keys_data[bot['id']]['deposit_address']
                bot['whale_address'] = keys_data[bot['id']]['whale_address']
                bot['vault_secret'] = keys_data[bot['id']]['vault_secret']
                bot['whale_secret'] = keys_data[bot['id']].get('whale_secret', '')
        
        print(f"[VAULT] Keys loaded from {VAULT_KEYS_FILE}")
        return True
    except Exception as e:
        print(f"[VAULT] Error loading keys: {e}")
        return False

def initialize_bot_accounts():
    """Initialize Stellar accounts for each trading bot's vault"""
    
    if load_vault_keys():
        print("[VAULT] Using existing vault accounts:")
        for bot in TRADING_BOTS:
            print(f"  {bot['name']}: {bot['deposit_address'][:20]}...")
        return
    
    print("[VAULT] Creating new vault accounts...")
    
    for bot in TRADING_BOTS:
        # Generate vault keypair
        vault_keypair = Keypair.random()
        bot['deposit_address'] = vault_keypair.public_key
        bot['vault_secret'] = vault_keypair.secret
        
        # Generate whale keypair
        whale_keypair = Keypair.random()
        bot['whale_address'] = whale_keypair.public_key
        bot['whale_secret'] = whale_keypair.secret
        
        print(f"\n[{bot['name']}]")
        print(f"  Vault: {bot['deposit_address'][:24]}...")
        print(f"  Whale: {bot['whale_address'][:24]}...")
        
        # Fund accounts via friendbot
        try:
            response = requests.get(f"{FRIENDBOT_URL}?addr={bot['deposit_address']}")
            if response.status_code == 200:
                print(f"  ✓ Vault funded")
            
            response = requests.get(f"{FRIENDBOT_URL}?addr={bot['whale_address']}")
            if response.status_code == 200:
                print(f"  ✓ Whale funded")
        except Exception as e:
            print(f"  ✗ Funding error: {e}")
    
    save_vault_keys()

def get_user_session(user_public_key):
    """Get or create user session"""
    if user_public_key not in user_sessions:
        user_sessions[user_public_key] = {
            "public_key": user_public_key,
            "active_bots": {}
        }
    return user_sessions[user_public_key]

def generate_daily_performance():
    """Generate random daily performance between -3% and +5%"""
    return round(random.uniform(-3.0, 5.0), 2)

# ============== DEBUG ENDPOINTS ==============

@app.route('/debug/vaults', methods=['GET'])
def debug_vaults():
    """Debug endpoint to check vault balances"""
    vault_info = []
    
    for bot in TRADING_BOTS:
        vault_balance = "0"
        whale_balance = "0"
        
        try:
            account = server.accounts().account_id(bot['deposit_address']).call()
            vault_balance = next(
                (b['balance'] for b in account.get('balances', []) if b['asset_type'] == 'native'),
                '0'
            )
        except:
            pass
            
        try:
            account = server.accounts().account_id(bot['whale_address']).call()
            whale_balance = next(
                (b['balance'] for b in account.get('balances', []) if b['asset_type'] == 'native'),
                '0'
            )
        except:
            pass
        
        vault_info.append({
            "bot_id": bot['id'],
            "bot_name": bot['name'],
            "vault_address": bot['deposit_address'],
            "vault_balance": vault_balance,
            "whale_address": bot['whale_address'],
            "whale_balance": whale_balance,
            "vault_explorer": f"https://stellar.expert/explorer/testnet/account/{bot['deposit_address']}",
            "whale_explorer": f"https://stellar.expert/explorer/testnet/account/{bot['whale_address']}"
        })
    
    return jsonify({"success": True, "vaults": vault_info})

@app.route('/debug/sessions', methods=['GET'])
def debug_sessions():
    """Debug endpoint to see all user sessions"""
    return jsonify({"success": True, "sessions": user_sessions})

# ============== MAIN API ENDPOINTS ==============

@app.route('/bots', methods=['GET'])
def get_bots():
    """Return list of available trading bots"""
    bots_public = []
    for bot in TRADING_BOTS:
        bots_public.append({
            "id": bot['id'],
            "name": bot['name'],
            "strategy": bot['strategy'],
            "commission_rate": bot['commission_rate'],
            "min_commission_deposit": bot['min_commission_deposit'],
            "deposit_address": bot['deposit_address'],
            "whale_address": bot['whale_address']
        })
    return jsonify({"success": True, "bots": bots_public})

@app.route('/status', methods=['GET'])
def get_status():
    """Get user's current status"""
    public_key = request.args.get('public_key')
    
    if not public_key:
        return jsonify({"success": False, "error": "Missing public_key"}), 400
    
    session = get_user_session(public_key)
    
    # Convert active_bots dict to list with status
    active_bots_list = []
    for bot_id, bot_data in session['active_bots'].items():
        bot_info = bot_data.copy()
        bot_info['bot_id'] = bot_id
        # Check if bot is still accessible (has commission balance)
        bot_info['is_accessible'] = bot_data['commission_balance'] > 0
        active_bots_list.append(bot_info)
    
    return jsonify({
        "success": True,
        "user_public_key": public_key,
        "active_bots": active_bots_list
    })

@app.route('/create-deposit-tx', methods=['POST'])
def create_deposit_tx():
    """Create a deposit transaction for Freighter to sign"""
    try:
        data = request.json
        bot_id = data.get('bot_id')
        user_public_key = data.get('user_public_key')
        amount = data.get('amount', '10')
        
        print(f"[CREATE-TX] bot={bot_id}, user={user_public_key[:16]}..., amount={amount}")
        
        if not all([bot_id, user_public_key]):
            return jsonify({"success": False, "error": "Missing parameters"}), 400
        
        bot = next((b for b in TRADING_BOTS if b['id'] == bot_id), None)
        if not bot:
            return jsonify({"success": False, "error": "Bot not found"}), 404
        
        try:
            source_account = server.load_account(user_public_key)
        except NotFoundError:
            return jsonify({
                "success": False,
                "error": "Account not found. Fund it at https://laboratory.stellar.org"
            }), 400
        
        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=NETWORK_PASSPHRASE,
                base_fee=100
            )
            .append_payment_op(
                destination=bot['deposit_address'],
                asset=Asset.native(),
                amount=str(amount)
            )
            .set_timeout(300)
            .build()
        )
        
        return jsonify({
            "success": True,
            "xdr": transaction.to_xdr(),
            "network_passphrase": NETWORK_PASSPHRASE
        })
        
    except Exception as e:
        print(f"[CREATE-TX] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/submit-transaction', methods=['POST'])
def submit_transaction():
    """Submit a signed transaction to Stellar"""
    from stellar_sdk import TransactionEnvelope
    
    try:
        data = request.json
        signed_xdr = data.get('signed_xdr')
        bot_id = data.get('bot_id')
        user_public_key = data.get('user_public_key')
        amount = float(data.get('amount', 10))
        is_topup = data.get('is_topup', False)
        
        print(f"[SUBMIT-TX] bot={bot_id}, user={user_public_key[:16]}..., amount={amount}, topup={is_topup}")
        
        if not signed_xdr:
            return jsonify({"success": False, "error": "Missing signed_xdr"}), 400
        
        response = server.submit_transaction(
            TransactionEnvelope.from_xdr(signed_xdr, network_passphrase=NETWORK_PASSPHRASE)
        )
        
        tx_hash = response.get('hash', '')
        print(f"[SUBMIT-TX] SUCCESS! Hash: {tx_hash[:16]}...")
        
        # Initialize or update bot tracking
        if bot_id and user_public_key:
            session = get_user_session(user_public_key)
            
            if is_topup and bot_id in session['active_bots']:
                # Top-up existing subscription
                session['active_bots'][bot_id]['commission_balance'] += amount
                session['active_bots'][bot_id]['total_deposited'] += amount
                print(f"[SUBMIT-TX] Top-up: +{amount} XLM commission")
            else:
                # New subscription
                session['active_bots'][bot_id] = {
                    # Commission tracking (real XLM)
                    "commission_balance": amount,  # XLM available for commission payments
                    "total_deposited": amount,     # Total XLM ever deposited
                    "total_commission_paid": 0,    # Total XLM paid as commission
                    
                    # Trading simulation (virtual $)
                    "simulation_balance": STARTING_SIMULATION_BALANCE,  # Virtual $ balance
                    "starting_balance": STARTING_SIMULATION_BALANCE,
                    "total_profit": 0,             # Total $ profit/loss
                    
                    # High Water Mark - highest balance ever reached (for commission calc)
                    "high_water_mark": STARTING_SIMULATION_BALANCE,
                    
                    # Day tracking
                    "current_day": 0,
                    "daily_history": [
                        {
                            "day": 0,
                            "performance_percent": 0,
                            "profit_usd": 0,
                            "commission_xlm": 0,
                            "simulation_balance": STARTING_SIMULATION_BALANCE,
                            "commission_balance": amount,
                            "high_water_mark": STARTING_SIMULATION_BALANCE
                        }
                    ],
                    
                    # Status
                    "is_accessible": True,
                    "deposit_tx": tx_hash
                }
                print(f"[SUBMIT-TX] New subscription: {amount} XLM, ${STARTING_SIMULATION_BALANCE} simulation")
        
        return jsonify({
            "success": True,
            "transaction_hash": tx_hash,
            "explorer_url": f"https://stellar.expert/explorer/testnet/tx/{tx_hash}"
        })
        
    except Exception as e:
        print(f"[SUBMIT-TX] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/simulate-day', methods=['POST'])
def simulate_day():
    """Simulate next day's trading performance"""
    try:
        data = request.json
        bot_id = data.get('bot_id')
        user_public_key = data.get('user_public_key')
        
        print(f"[SIMULATE-DAY] bot={bot_id}, user={user_public_key[:16]}...")
        
        if not all([bot_id, user_public_key]):
            return jsonify({"success": False, "error": "Missing parameters"}), 400
        
        session = get_user_session(user_public_key)
        
        if bot_id not in session['active_bots']:
            return jsonify({"success": False, "error": "Bot'a abone değilsiniz"}), 400
        
        bot = next((b for b in TRADING_BOTS if b['id'] == bot_id), None)
        if not bot:
            return jsonify({"success": False, "error": "Bot not found"}), 404
        
        bot_session = session['active_bots'][bot_id]
        
        # Check if bot is still accessible
        if bot_session['commission_balance'] <= 0:
            bot_session['is_accessible'] = False
            return jsonify({
                "success": False,
                "error": "Commission balance depleted! Add more to continue.",
                "needs_topup": True
            }), 400
        
        # Generate random daily performance
        performance_percent = generate_daily_performance()
        
        # Calculate profit in USD (simulation)
        profit_usd = bot_session['simulation_balance'] * (performance_percent / 100)
        
        # New balance after this day
        new_balance = bot_session['simulation_balance'] + profit_usd
        
        # Get current high water mark (initialize if not exists for older sessions)
        high_water_mark = bot_session.get('high_water_mark', bot_session['starting_balance'])
        
        # XLM/USD rate - 1 XLM = $0.40 (more realistic testnet rate)
        xlm_usd_rate = 0.40  # 1 XLM = $0.40
        commission_xlm = 0
        commission_usd = 0
        
        # HIGH WATER MARK SYSTEM:
        # Only charge commission on NEW profits above the previous high water mark
        # Example: HWM=$1005, balance dropped to $1003, now $1007
        #          Only charge on $1007-$1005 = $2, not on $1007-$1003 = $4
        
        if new_balance > high_water_mark:
            # We have NEW profits above previous high water mark!
            taxable_profit = new_balance - high_water_mark
            commission_usd = taxable_profit * (bot['commission_rate'] / 100)
            
            # Convert USD commission to XLM
            commission_xlm = commission_usd / xlm_usd_rate
            
            # Cap commission to available balance
            if commission_xlm > bot_session['commission_balance']:
                commission_xlm = bot_session['commission_balance']
            
            # Update high water mark to new balance
            bot_session['high_water_mark'] = new_balance
            print(f"[SIMULATE-DAY] New HWM: ${new_balance:.2f} (was ${high_water_mark:.2f})")
        else:
            # Balance is at or below high water mark - no commission
            print(f"[SIMULATE-DAY] Below HWM: ${new_balance:.2f} < ${high_water_mark:.2f} - No commission")
        
        # Update simulation balance (virtual $)
        bot_session['simulation_balance'] = new_balance
        bot_session['total_profit'] += profit_usd
        
        # Deduct commission from real XLM balance
        bot_session['commission_balance'] -= commission_xlm
        bot_session['total_commission_paid'] += commission_xlm
        
        # Update day
        bot_session['current_day'] += 1
        
        # Check if bot becomes inaccessible
        if bot_session['commission_balance'] <= 0:
            bot_session['is_accessible'] = False
        
        # Add to daily history
        new_day = {
            "day": bot_session['current_day'],
            "performance_percent": performance_percent,
            "profit_usd": round(profit_usd, 2),
            "commission_xlm": round(commission_xlm, 4),
            "simulation_balance": round(bot_session['simulation_balance'], 2),
            "commission_balance": round(bot_session['commission_balance'], 4),
            "high_water_mark": round(bot_session.get('high_water_mark', bot_session['starting_balance']), 2)
        }
        bot_session['daily_history'].append(new_day)
        
        print(f"[SIMULATE-DAY] Day {bot_session['current_day']}: {performance_percent}% | Profit: ${profit_usd:.2f} | Commission: {commission_xlm:.4f} XLM")
        
        # If commission > 0, transfer to whale
        tx_hash = None
        if commission_xlm > 0.0001:
            try:
                vault_keypair = Keypair.from_secret(bot['vault_secret'])
                vault_account = server.load_account(bot['deposit_address'])
                
                transaction = (
                    TransactionBuilder(
                        source_account=vault_account,
                        network_passphrase=NETWORK_PASSPHRASE,
                        base_fee=100
                    )
                    .append_payment_op(
                        destination=bot['whale_address'],
                        asset=Asset.native(),
                        amount=str(round(commission_xlm, 7))
                    )
                    .set_timeout(30)
                    .build()
                )
                
                transaction.sign(vault_keypair)
                response = server.submit_transaction(transaction)
                tx_hash = response.get('hash')
                print(f"[SIMULATE-DAY] Commission transferred: {tx_hash[:16]}...")
                
            except Exception as e:
                print(f"[SIMULATE-DAY] Commission transfer failed: {e}")
        
        return jsonify({
            "success": True,
            "day": bot_session['current_day'],
            "performance_percent": performance_percent,
            "profit_usd": round(profit_usd, 2),
            "commission_xlm": round(commission_xlm, 4),
            "simulation_balance": round(bot_session['simulation_balance'], 2),
            "commission_balance": round(bot_session['commission_balance'], 4),
            "total_profit": round(bot_session['total_profit'], 2),
            "total_commission_paid": round(bot_session['total_commission_paid'], 4),
            "is_accessible": bot_session['is_accessible'],
            "commission_tx": tx_hash,
            "daily_history": bot_session['daily_history']
        })
        
    except Exception as e:
        print(f"[SIMULATE-DAY] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/reset-simulation', methods=['POST'])
def reset_simulation():
    """Reset simulation and refund all commissions from whale back to vault"""
    try:
        data = request.json
        bot_id = data.get('bot_id')
        user_public_key = data.get('user_public_key')
        
        print(f"[RESET] bot={bot_id}, user={user_public_key[:16]}...")
        
        if not all([bot_id, user_public_key]):
            return jsonify({"success": False, "error": "Missing parameters"}), 400
        
        session = get_user_session(user_public_key)
        
        if bot_id not in session['active_bots']:
            return jsonify({"success": False, "error": "You are not subscribed to this bot"}), 400
        
        bot = next((b for b in TRADING_BOTS if b['id'] == bot_id), None)
        if not bot:
            return jsonify({"success": False, "error": "Bot not found"}), 404
        
        bot_session = session['active_bots'][bot_id]
        total_commission = bot_session['total_commission_paid']
        original_deposit = bot_session['total_deposited']
        
        refund_tx = None
        
        # Refund commissions from whale back to vault
        if total_commission > 0.0001:
            try:
                whale_keypair = Keypair.from_secret(bot['whale_secret'])
                whale_account = server.load_account(bot['whale_address'])
                
                transaction = (
                    TransactionBuilder(
                        source_account=whale_account,
                        network_passphrase=NETWORK_PASSPHRASE,
                        base_fee=100
                    )
                    .append_payment_op(
                        destination=bot['deposit_address'],
                        asset=Asset.native(),
                        amount=str(round(total_commission, 7))
                    )
                    .set_timeout(30)
                    .build()
                )
                
                transaction.sign(whale_keypair)
                response = server.submit_transaction(transaction)
                refund_tx = response.get('hash')
                print(f"[RESET] Refunded {total_commission} XLM: {refund_tx[:16]}...")
                
            except Exception as e:
                print(f"[RESET] Refund failed: {e}")
        
        # Reset session
        session['active_bots'][bot_id] = {
            "commission_balance": original_deposit,
            "total_deposited": original_deposit,
            "total_commission_paid": 0,
            "simulation_balance": STARTING_SIMULATION_BALANCE,
            "starting_balance": STARTING_SIMULATION_BALANCE,
            "total_profit": 0,
            "high_water_mark": STARTING_SIMULATION_BALANCE,
            "current_day": 0,
            "daily_history": [
                {
                    "day": 0,
                    "performance_percent": 0,
                    "profit_usd": 0,
                    "commission_xlm": 0,
                    "simulation_balance": STARTING_SIMULATION_BALANCE,
                    "commission_balance": original_deposit,
                    "high_water_mark": STARTING_SIMULATION_BALANCE
                }
            ],
            "is_accessible": True,
            "deposit_tx": bot_session.get('deposit_tx', '')
        }
        
        return jsonify({
            "success": True,
            "message": f"Reset complete! {round(total_commission, 4)} XLM commission refunded.",
            "refunded_amount": round(total_commission, 4),
            "refund_tx": refund_tx,
            "new_commission_balance": original_deposit,
            "new_simulation_balance": STARTING_SIMULATION_BALANCE
        })
        
    except Exception as e:
        print(f"[RESET] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/topup', methods=['POST'])
def topup_commission():
    """Add more commission balance to existing bot subscription"""
    try:
        data = request.json
        bot_id = data.get('bot_id')
        user_public_key = data.get('user_public_key')
        amount = data.get('amount', '10')
        
        print(f"[TOPUP] Creating topup tx for bot={bot_id}, amount={amount}")
        
        if not all([bot_id, user_public_key]):
            return jsonify({"success": False, "error": "Missing parameters"}), 400
        
        bot = next((b for b in TRADING_BOTS if b['id'] == bot_id), None)
        if not bot:
            return jsonify({"success": False, "error": "Bot not found"}), 404
        
        try:
            source_account = server.load_account(user_public_key)
        except NotFoundError:
            return jsonify({
                "success": False,
                "error": "Account not found"
            }), 400
        
        transaction = (
            TransactionBuilder(
                source_account=source_account,
                network_passphrase=NETWORK_PASSPHRASE,
                base_fee=100
            )
            .append_payment_op(
                destination=bot['deposit_address'],
                asset=Asset.native(),
                amount=str(amount)
            )
            .set_timeout(300)
            .build()
        )
        
        return jsonify({
            "success": True,
            "xdr": transaction.to_xdr(),
            "network_passphrase": NETWORK_PASSPHRASE,
            "is_topup": True
        })
        
    except Exception as e:
        print(f"[TOPUP] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/withdraw', methods=['POST'])
def withdraw():
    """Withdraw remaining commission balance back to user"""
    try:
        data = request.json
        bot_id = data.get('bot_id')
        user_public_key = data.get('user_public_key')
        
        print(f"[WITHDRAW] bot={bot_id}, user={user_public_key[:16]}...")
        
        if not all([bot_id, user_public_key]):
            return jsonify({"success": False, "error": "Missing parameters"}), 400
        
        session = get_user_session(user_public_key)
        
        if bot_id not in session['active_bots']:
            return jsonify({"success": False, "error": "You are not subscribed to this bot"}), 400
        
        bot = next((b for b in TRADING_BOTS if b['id'] == bot_id), None)
        if not bot:
            return jsonify({"success": False, "error": "Bot not found"}), 404
        
        bot_session = session['active_bots'][bot_id]
        remaining = bot_session['commission_balance']
        
        if remaining <= 0.0001:
            del session['active_bots'][bot_id]
            return jsonify({
                "success": True,
                "message": "No balance to withdraw",
                "amount_withdrawn": 0
            })
        
        try:
            vault_keypair = Keypair.from_secret(bot['vault_secret'])
            vault_account = server.load_account(bot['deposit_address'])
            
            transaction = (
                TransactionBuilder(
                    source_account=vault_account,
                    network_passphrase=NETWORK_PASSPHRASE,
                    base_fee=100
                )
                .append_payment_op(
                    destination=user_public_key,
                    asset=Asset.native(),
                    amount=str(round(remaining, 7))
                )
                .set_timeout(30)
                .build()
            )
            
            transaction.sign(vault_keypair)
            response = server.submit_transaction(transaction)
            
            tx_hash = response.get('hash', '')
            print(f"[WITHDRAW] SUCCESS! {remaining} XLM -> {tx_hash[:16]}...")
            
            del session['active_bots'][bot_id]
            
            return jsonify({
                "success": True,
                "amount_withdrawn": round(remaining, 4),
                "transaction_hash": tx_hash,
                "explorer_url": f"https://stellar.expert/explorer/testnet/tx/{tx_hash}"
            })
            
        except Exception as e:
            print(f"[WITHDRAW] Transaction error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        
    except Exception as e:
        print(f"[WITHDRAW] Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "network": "stellar-testnet",
        "horizon": HORIZON_URL
    })

if __name__ == '__main__':
    print("=" * 60)
    print("Profit Sharing App - Commission Based Access")
    print("=" * 60)
    print(f"Network: Stellar Testnet")
    print(f"Horizon: {HORIZON_URL}")
    print(f"Starting Simulation Balance: ${STARTING_SIMULATION_BALANCE}")
    print()
    
    initialize_bot_accounts()
    
    print()
    print("=" * 60)
    print("ENDPOINTS:")
    print("  GET  /bots                - List all bots")
    print("  GET  /status              - Get user status")
    print("  POST /create-deposit-tx   - Create deposit transaction")
    print("  POST /submit-transaction  - Submit signed transaction")
    print("  POST /simulate-day        - Simulate next trading day")
    print("  POST /reset-simulation    - Reset & refund commissions")
    print("  POST /topup               - Add more commission balance")
    print("  POST /withdraw            - Withdraw commission balance")
    print("  GET  /debug/vaults        - Debug vault balances")
    print("=" * 60)
    print()
    print("Starting on port 5328...")
    
    app.run(host='127.0.0.1', port=5328, debug=True)
