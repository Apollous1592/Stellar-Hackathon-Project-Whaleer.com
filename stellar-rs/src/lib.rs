#![no_std]
use soroban_sdk::{contract, contractimpl, contracttype, Address, Env, Symbol, token, symbol_short};

// --- VERİ YAPILARI ---

#[contracttype]
#[derive(Clone)]
pub enum DataKey {
    Admin,                  // Whaleer Backend Adresi (Yönetici)
    Vault(u64, Address),    // (BotID, UserAddress) -> VaultObj
}

#[contracttype]
#[derive(Clone)]
pub struct VaultObj {
    pub developer: Address,    // Botu yapan kişi
    pub platform: Address,     // Whaleer cüzdanı
    pub asset: Address,        // Kullanılan Token (XLM/USDC)
    pub profit_share_bps: u32, // Geliştirici Payı (Örn: 2000 = %20)
    pub platform_cut_bps: u32, // Platform Payı (Örn: 1000 = %10)
    pub balance: i128,         // Kasadaki Bakiye
    pub is_active: bool,       // Aktif mi?
}

// --- OLAYLAR (EVENTS) ---
const EVT_DEPOSIT: Symbol = symbol_short!("deposit");
const EVT_WITHDRAW: Symbol = symbol_short!("withdraw");
const EVT_SETTLED: Symbol = symbol_short!("settled");
const EVT_INSUFF: Symbol = symbol_short!("insuff"); // Yetersiz Bakiye

#[contract]
pub struct ProfitSharingVault;

#[contractimpl]
impl ProfitSharingVault {

    // 1. INIT: Kontratı başlatır ve Yöneticiyi (Backend) atar.
    pub fn init(env: Env, admin: Address) {
        if env.storage().instance().has(&DataKey::Admin) {
            panic!("Already initialized");
        }
        env.storage().instance().set(&DataKey::Admin, &admin);
    }

    // 2. INIT_VAULT: Yeni bir kasa oluşturur. (Sadece Admin çağırabilir)
    pub fn init_vault(
        env: Env,
        bot_id: u64,
        user: Address,
        developer: Address,
        platform: Address,
        asset: Address,
        profit_share_bps: u32,
        platform_cut_bps: u32
    ) {
        let admin: Address = env.storage().instance().get(&DataKey::Admin).expect("Not initialized");
        admin.require_auth(); // Admin imzası şart

        // BPS Validasyonu (0 - 10,000 arası olmalı)
        if profit_share_bps > 10_000 {
            panic!("Invalid profit_share_bps: max 10000");
        }
        if platform_cut_bps > 10_000 {
            panic!("Invalid platform_cut_bps: max 10000");
        }

        let key = DataKey::Vault(bot_id, user.clone());
        
        // Overwrite koruması
        if env.storage().persistent().has(&key) {
            panic!("Vault already exists for this bot and user");
        }
        
        let new_vault = VaultObj {
            developer,
            platform,
            asset,
            profit_share_bps,
            platform_cut_bps,
            balance: 0,
            is_active: true,
        };

        env.storage().persistent().set(&key, &new_vault);
    }

    // 3. DEPOSIT: Kullanıcı kasaya para yükler.
    pub fn deposit(env: Env, bot_id: u64, user: Address, amount: i128) {
        user.require_auth(); // Kullanıcı onayı şart
        
        if amount <= 0 { panic!("Amount must be positive"); }

        let key = DataKey::Vault(bot_id, user.clone());
        let mut vault: VaultObj = env.storage().persistent().get(&key).expect("Vault not found");

        // Kullanıcıdan Kontrata Transfer
        let client = token::Client::new(&env, &vault.asset);
        client.transfer(&user, &env.current_contract_address(), &amount);

        // Bakiyeyi güncelle
        vault.balance += amount;
        
        // ÖNEMLİ: Para yüklenince pasif olan vault tekrar aktif olur!
        vault.is_active = true; 
        
        env.storage().persistent().set(&key, &vault);

        env.events().publish((EVT_DEPOSIT, user), (bot_id, amount));
    }

    // 4. WITHDRAW: Kullanıcı parasını geri çeker.
    pub fn withdraw(env: Env, bot_id: u64, user: Address, amount: i128) {
        user.require_auth();

        if amount <= 0 { panic!("Amount must be positive"); }

        let key = DataKey::Vault(bot_id, user.clone());
        let mut vault: VaultObj = env.storage().persistent().get(&key).expect("Vault not found");

        if amount > vault.balance {
            panic!("Insufficient vault balance");
        }

        // Kontrattan Kullanıcıya Transfer
        let client = token::Client::new(&env, &vault.asset);
        client.transfer(&env.current_contract_address(), &user, &amount);

        vault.balance -= amount;
        env.storage().persistent().set(&key, &vault);

        env.events().publish((EVT_WITHDRAW, user), (bot_id, amount));
    }

    // 5. SETTLE_PROFIT: Kâr dağıtımı (Sadece Admin/Backend çağırır)
    pub fn settle_profit(env: Env, bot_id: u64, user: Address, profit_amount: i128) {
        let admin: Address = env.storage().instance().get(&DataKey::Admin).expect("Not initialized");
        admin.require_auth(); // Backend imzası şart

        if profit_amount <= 0 { panic!("Profit amount must be positive"); }

        let key = DataKey::Vault(bot_id, user.clone());
        let mut vault: VaultObj = env.storage().persistent().get(&key).expect("Vault not found");

        // Eğer vault zaten pasifse işlem yapma ve çık
        if !vault.is_active { 
            return; 
        }

        // --- HESAPLAMA ---
        let total_commission = (profit_amount * vault.profit_share_bps as i128) / 10_000;

        // Bakiye Kontrolü
        if vault.balance < total_commission {
            // Yetersiz Bakiye Eventi
            env.events().publish((EVT_INSUFF, user.clone()), (bot_id, total_commission, vault.balance));
            
            // --- GÜNCELLEME BURADA ---
            // Vault'u pasife çekiyoruz. 
            // Kullanıcı tekrar 'deposit' yapana kadar bu vault kilitli kalacak.
            vault.is_active = false;
            env.storage().persistent().set(&key, &vault);
            
            return;
        }

        // Platform Payı
        let platform_fee = (total_commission * vault.platform_cut_bps as i128) / 10_000;
        let dev_fee = total_commission - platform_fee;

        // --- TRANSFERLER ---
        let client = token::Client::new(&env, &vault.asset);

        // Platforma öde
        if platform_fee > 0 {
            client.transfer(&env.current_contract_address(), &vault.platform, &platform_fee);
        }

        // Geliştiriciye öde
        if dev_fee > 0 {
            client.transfer(&env.current_contract_address(), &vault.developer, &dev_fee);
        }

        // Bakiyeyi düş ve kaydet
        vault.balance -= total_commission;
        
        // İşlem başarılı, aktif kalmaya devam ediyor
        env.storage().persistent().set(&key, &vault);

        env.events().publish((EVT_SETTLED, user), (bot_id, profit_amount, total_commission));
    }

    // 6. GET_VAULT: View Fonksiyonu
    pub fn get_vault(env: Env, bot_id: u64, user: Address) -> VaultObj {
        let key = DataKey::Vault(bot_id, user.clone());
        env.storage().persistent().get(&key).expect("Vault not found")
    }
}