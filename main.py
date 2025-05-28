
import requests, time, json
from solders.keypair import Keypair
from solders.rpc.api import Client
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import Transaction
from base64 import b64decode

# === KONFIGURASI ===
BUY_AMOUNT_SOL = 0.05
TAKE_PROFIT_MULTIPLIER = 2.0
TRAILING_STOP_DROP = 0.3
PUMPFUN_API = "https://api.pump.fun/markets/recent"
RPC = "https://api.mainnet-beta.solana.com"
JUPITER_PRICE_API = "https://price.jup.ag/v4/price?ids="

# === LOAD WALLET ===
with open("my-autobuy-wallet.json", "r") as f:
    key = json.load(f)
    wallet = Keypair.from_bytes(bytes(key))
    my_address = wallet.pubkey()

client = Client(RPC)
sudah_beli = {}

# === AMBIL TOKEN BARU ===
def get_recent_tokens():
    try:
        res = requests.get(PUMPFUN_API).json()
        return res["markets"]
    except:
        return []

# === AMBIL HARGA TOKEN ===
def get_token_price(token_mint):
    try:
        res = requests.get(f"{JUPITER_PRICE_API}{token_mint}")
        data = res.json()
        return float(data['data'][token_mint]['price'])
    except:
        return None

# === BELI TOKEN ===
def buy_token(token_address):
    try:
        to_pubkey = Pubkey.from_string(token_address[:44])
        lamports = int(BUY_AMOUNT_SOL * 1_000_000_000)
        tx = Transaction()
        instr = transfer(TransferParams(
            from_pubkey=my_address,
            to_pubkey=to_pubkey,
            lamports=lamports
        ))
        tx.add(instr)
        tx.sign([wallet])
        resp = client.send_transaction(tx)
        print("[BELI]", f"https://solscan.io/tx/{resp.value}")
        return True
    except Exception as e:
        print("Gagal beli:", e)
        return False

# === MONITOR DAN JUAL ===
def monitor_and_sell(token_id, harga_beli, token_mint, jumlah_token):
    harga_puncak = harga_beli
    while True:
        harga_skrg = get_token_price(token_mint)
        if not harga_skrg:
            time.sleep(15)
            continue
        if harga_skrg > harga_puncak:
            harga_puncak = harga_skrg
        if harga_skrg <= harga_puncak * (1 - TRAILING_STOP_DROP):
            print("TRAILING STOP TERPICU >> Jual token", token_id)
            break
        print(f"[MONITOR] {token_id} | Sekarang: {harga_skrg:.4f} | Tertinggi: {harga_puncak:.4f}")
        time.sleep(15)

# === LOOP UTAMA ===
while True:
    print("Cek token baru...")
    tokens = get_recent_tokens()
    for token in tokens:
        token_id = token.get("id")
        token_mint = token.get("id")
        if token_id in sudah_beli:
            continue
        success = buy_token(token_id)
        if success:
            harga_awal = get_token_price(token_mint)
            if harga_awal:
                sudah_beli[token_id] = True
                jumlah_token = 1000000  # placeholder
                monitor_and_sell(token_id, harga_awal, token_mint, jumlah_token)
            else:
                print(">> Gagal ambil harga awal")
        time.sleep(15)
