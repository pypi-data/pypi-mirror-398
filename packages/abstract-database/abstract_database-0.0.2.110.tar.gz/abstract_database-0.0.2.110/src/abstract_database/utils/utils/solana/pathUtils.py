from .imports import os
def get_abs_path():
    return os.path.abspath(__name__)
def get_abs_dir():
    return os.path.dirname(get_abs_path())
def get_wallets_directory():
    wallets_dir = os.path.join(get_abs_dir(),'wallets')
    os.makedirs(wallets_dir,exist_ok=True)
    return wallets_dir
def get_user_wallet_path(walletAddress):
    wallet_dir = os.path.join(get_wallets_directory(),walletAddress)
    os.makedirs(wallet_dir,exist_ok=True)
    return wallet_dir
def get_user_wallet_mint_path(walletAddress,mint):
    wallet_dir = get_user_wallet_path(walletAddress)
    mint_dir = os.path.join(wallet_dir,mint)
    os.makedirs(mint_dir,exist_ok=True)
    return mint_dir
def get_user_wallet_mint_liquidity_pool_path(walletAddress,mint,liquidity_pool):
    mint_dir = get_user_wallet_mint_path(walletAddress,mint)
    liquidity_pool_dir = os.path.join(mint_dir,liquidity_pool)
    os.makedirs(liquidity_pool_dir,exist_ok=True)
    return liquidity_pool_dir

def get_liquidity_pools_directory():
    liquidity_pools_dir = os.path.join(get_abs_dir(),'liquidity_pools')
    os.makedirs(liquidity_pools_dir,exist_ok=True)
    return liquidity_pools_dir
def get_liquidity_pool_path(liquidity_pool):
    liquidity_pool_dir = os.path.join(get_liquidity_pools_directory(),liquidity_pool)
    os.makedirs(liquidity_pool_dir,exist_ok=True)
    return liquidity_pool_dir
def get_liquidity_pool_user_wallet_path(liquidity_pool,walletAddress):
    liquidity_pool_dir = get_liquidity_pool_path(liquidity_pool)
    liquidity_pool_user_wallet_dir = os.path.join(liquidity_pool_dir,walletAddress)
    os.makedirs(liquidity_pool_user_wallet_dir,exist_ok=True)
    return liquidity_pool_user_wallet_dir
def get_liquidity_pool_user_wallet_chart_path(liquidity_pool,walletAddress):
    liquidity_pool_user_wallet_path = get_liquidity_pool_user_wallet_path(liquidity_pool,walletAddress)
    chart_path = os.path.join(liquidity_pool_user_wallet_path,'volumeData.png')
    return chart_path
def get_liquidity_pool_chart_path(liquidity_pool):
    liquidity_pool_path = get_liquidity_pool_path(liquidity_pool)
    chart_path = os.path.join(liquidity_pool_path,'TransactionData.png')
    return chart_path
