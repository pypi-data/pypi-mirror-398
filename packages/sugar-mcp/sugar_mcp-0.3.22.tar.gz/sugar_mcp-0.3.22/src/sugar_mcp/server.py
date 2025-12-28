import os
import sys
import time
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from netmind_sugar.chains import get_chain, Token, Price, LiquidityPool, Quote, LiquidityPoolForSwap
from netmind_sugar.pool import Amount, LiquidityPoolEpoch
from pydantic import Field, BaseModel
from web3 import Web3

from typing import Optional, List, Tuple
from sugar_mcp.cache import _get_cached_pools, _get_pool_from_cache, _get_pools_from_chain, _get_pool_from_chain, start_background_updates, set_enabled_chains, set_pool_filtering, set_cache_duration_minutes, configure_cache, CacheConfig, start_cache_system


mcp = FastMCP("sugar-mcp", port=8089, host="0.0.0.0")


class TokenInfo(BaseModel):
    chain_id: str = Field(..., description="Chain ID, e.g., '10' for OPChain, '8453' for BaseChain")
    chain_name: str = Field(..., description="Chain name, e.g., 'OPChain', 'BaseChain'")
    token_address: str = Field(..., description="Token contract address")
    symbol: str = Field(..., description="Token symbol, e.g., 'USDC', 'VELO'")
    decimals: int = Field(..., description="Number of decimals for the token")
    listed: bool = Field(..., description="Whether the token is listed")
    wrapped_token_address: str = Field(default="", description="Wrapped token address")

    @staticmethod
    def from_token(t: Token):
        return TokenInfo(
            chain_id=t.chain_id,
            chain_name=t.chain_name,
            token_address=t.token_address,
            symbol=t.symbol,
            decimals=t.decimals,
            listed=t.listed,
            wrapped_token_address=t.wrapped_token_address if t.wrapped_token_address else "",
        )

class PriceInfo(BaseModel):
    token: TokenInfo = Field(..., description="Token information")
    price: float = Field(..., description="Price in stable token")

    @staticmethod
    def from_price(p: Price):
        token_info = TokenInfo.from_token(p.token)
        return PriceInfo(token=token_info, price=p.price)

class AmountInfo(BaseModel):
    token: TokenInfo = Field(..., description="Token information")
    amount: int = Field(..., description="Amount in wei")
    price: PriceInfo = Field(..., description="Price information")
    #按产品需求添加字段
    amount_in_stable: float = Field(..., description="Amount in stable token")

    @staticmethod
    def from_amount(a: Amount):
        price_info = PriceInfo.from_price(a.price)
        return AmountInfo(token=TokenInfo.from_token(a.token), amount=a.amount, price=price_info, amount_in_stable=a.amount_in_stable)

class LiquidityPoolInfo(BaseModel):
    chain_id: str = Field(..., description="Chain ID")
    chain_name: str = Field(..., description="Chain name")
    lp: str = Field(..., description="Liquidity pool address")
    factory: str = Field(..., description="Factory address")
    symbol: str = Field(..., description="Pool symbol")
    type: int = Field(..., description="Pool type")
    is_stable: bool = Field(..., description="Whether the pool is stable")
    is_cl: bool = Field(..., description="Whether the pool is concentrated liquidity")
    total_supply: float = Field(..., description="Total supply of the pool")
    decimals: int = Field(..., description="Number of decimals for the pool")
    token0: TokenInfo = Field(..., description="Token0 information")
    reserve0: AmountInfo = Field(..., description="Token0 reserve amount")
    token1: TokenInfo = Field(..., description="Token1 information")
    reserve1: AmountInfo = Field(..., description="Token1 reserve amount")
    token0_fees: AmountInfo = Field(..., description="Token0 fees")
    token1_fees: AmountInfo = Field(..., description="Token1 fees")
    pool_fee: float = Field(..., description="Pool fee")
    gauge_total_supply: float = Field(..., description="Gauge total supply")
    emissions: Optional[AmountInfo] = Field(..., description="Emissions information")
    emissions_token: Optional[TokenInfo] = Field(..., description="Emissions token information")
    weekly_emissions: Optional[AmountInfo] = Field(..., description="Weekly emissions information")
    nfpm: str = Field(..., description="NFPM information")
    alm: str = Field(..., description="ALM information")
    #按产品需求追加字段
    tvl: float = Field(..., description="Total value locked in stable token")
    total_fees: float = Field(..., description="Total fees in stable token")
    pool_fee_percentage: float = Field(..., description="Pool fee percentage")
    volume_pct: float = Field(..., description="Volume percentage")
    volume: float = Field(..., description="Volume in stable token")
    token0_volume: float = Field(..., description="Token0 volume in stable token")
    token1_volume: float = Field(..., description="Token1 volume in stable token")
    gauge_staked_pct: float = Field(..., description="Gauge staked percentage")
    apr: float = Field(..., description="Annual percentage rate")

    @staticmethod
    def from_pool(p: LiquidityPool):
        return LiquidityPoolInfo(
            chain_id=p.chain_id,
            chain_name=p.chain_name,
            lp=p.lp,
            factory=p.factory,
            symbol=p.symbol,
            type=p.type,
            is_stable=p.is_stable,
            is_cl=p.is_cl,
            total_supply=p.total_supply,
            decimals=p.decimals,
            token0=TokenInfo.from_token(p.token0),
            reserve0=AmountInfo.from_amount(p.reserve0) if p.reserve0 else None,
            token1=TokenInfo.from_token(p.token1),
            reserve1=AmountInfo.from_amount(p.reserve1) if p.reserve1 else None,
            token0_fees=AmountInfo.from_amount(p.token0_fees) if p.token0_fees else None,
            token1_fees=AmountInfo.from_amount(p.token1_fees) if p.token1_fees else None,
            pool_fee=p.pool_fee,
            gauge_total_supply=p.gauge_total_supply,
            emissions=AmountInfo.from_amount(p.emissions) if p.emissions else None,
            emissions_token=TokenInfo.from_token(p.emissions_token) if p.emissions_token else None,
            weekly_emissions=AmountInfo.from_amount(p.weekly_emissions) if p.weekly_emissions else None,
            nfpm=p.nfpm,
            alm=p.alm,
            #追加字段赋值
            tvl=p.tvl,
            total_fees=p.total_fees,
            pool_fee_percentage=p.pool_fee_percentage,
            volume_pct=p.volume_pct,
            volume=p.volume_pct * (p.token0_fees.amount_in_stable + p.token1_fees.amount_in_stable if p.token0_fees and p.token1_fees else 0),
            token0_volume=p.token0_volume,
            token1_volume=p.token1_volume,
            gauge_staked_pct= (p.gauge_total_supply / p.total_supply * 100 if p.total_supply > 0 else 0),
            apr=p.apr
        )

class LiquidityPoolForSwapInfo(BaseModel):
    chain_id: str = Field(..., description="Chain ID")
    chain_name: str = Field(..., description="Chain name")
    lp: str = Field(..., description="Liquidity pool address")
    type: int = Field(..., description="Pool type")
    token0_address: str = Field(..., description="Token0 address")
    token1_address: str = Field(..., description="Token1 address")

    @staticmethod
    def from_pool(p: LiquidityPoolForSwap):
        return LiquidityPoolForSwapInfo(
            chain_id=p.chain_id,
            chain_name=p.chain_name,
            lp=p.lp,
            type=p.type,
            token0_address=p.token0_address,
            token1_address=p.token1_address
        )


def _convert_pools_to_swap_format(pools: List[LiquidityPool]) -> List[LiquidityPoolForSwap]:
    """
    Convert cached LiquidityPool objects to LiquidityPoolForSwap format.
    This allows using cached pool addresses while still getting real-time quotes.
    """
    result = []
    for p in pools:
        try:
            # Ensure all fields are the correct type
            pool_type = p.type
            if isinstance(pool_type, str):
                pool_type = int(pool_type)
            elif pool_type is None:
                pool_type = 0
            else:
                pool_type = int(pool_type)
            
            # Create the pool object and verify type is int
            pool_obj = LiquidityPoolForSwap(
                chain_id=str(p.chain_id),
                chain_name=str(p.chain_name),
                lp=str(p.lp),
                type=pool_type,
                token0_address=str(p.token0.token_address),
                token1_address=str(p.token1.token_address)
            )
            
            # Verify type is actually int (this will catch any type issues)
            if not isinstance(pool_obj.type, int):
                raise TypeError(f"Pool type must be int, got {type(pool_obj.type)}: {pool_obj.type}")
            
            result.append(pool_obj)
        except Exception as e:
            print(f"Error converting pool {p.lp}: {e}, type={type(p.type)}, value={p.type}")
            raise
    return result

class LiquidityPoolEpochInfo(BaseModel):
    ts: int = Field(..., description="Timestamp of the epoch")
    lp: str = Field(..., description="Liquidity pool address")
    pool: LiquidityPoolInfo = Field(..., description="Liquidity pool information")
    votes: int = Field(..., description="Number of votes")
    emissions: int = Field(..., description="Emissions amount")
    incentives: List[AmountInfo] = Field(..., description="List of incentives amounts")
    fees: List[AmountInfo] = Field(..., description="List of fees amounts")

    @staticmethod
    def from_epoch(e: LiquidityPoolEpoch):
        return LiquidityPoolEpochInfo(
            ts=e.ts,
            lp=e.lp,
            pool=LiquidityPoolInfo.from_pool(e.pool),
            votes=e.votes,
            emissions=e.emissions,
            incentives=[AmountInfo.from_amount(i) for i in e.incentives],
            fees=[AmountInfo.from_amount(f) for f in e.fees]
        )

class QuoteInputInfo(BaseModel):
    from_token: TokenInfo = Field(..., description="From token information")
    to_token: TokenInfo = Field(..., description="To token information")
    path: List[Tuple[LiquidityPoolForSwapInfo, bool]] = Field(..., description="Swap path as list of (pool, reversed) tuples")
    amount_in: int = Field(..., description="Input amount in wei")

    @staticmethod
    def from_quote_input(q: Quote):
        return QuoteInputInfo(
            from_token=TokenInfo.from_token(q.input.from_token),
            to_token=TokenInfo.from_token(q.input.to_token),
            path=[(LiquidityPoolForSwapInfo.from_pool(p), rev) for p, rev in q.input.path],
            amount_in=q.input.amount_in
        )

class QuoteInfo(BaseModel):
    input: QuoteInputInfo = Field(..., description="Quote input information")
    amount_out: int = Field(..., description="Output amount in wei")

    @staticmethod
    def from_quote(q: Quote):
        return QuoteInfo(
            input=QuoteInputInfo.from_quote_input(q),
            amount_out=q.amount_out
        )

@mcp.tool()
async def get_all_tokens(
    limit: int, offset: int, chainId: str = "10"
) -> List[TokenInfo]:
    """
    Retrieve all tokens supported by the protocol.

    Args:
        limit (int): Maximum number of tokens to return.
        offset (int): The starting point to retrieve tokens.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)

    Returns:
        List[Token]: A list of Token objects.
    """
    with get_chain(chainId) as chain:
        tokens = chain.get_tokens_page(limit, offset)
        tokens = list(
            map(
                lambda t: TokenInfo.from_token(
                    Token.from_tuple(t, chain_id=chain.chain_id, chain_name=chain.name)
                ),
                tokens,
            )
        )

        return tokens


@mcp.tool()
async def get_token_prices(token_address: str, chainId: str = "10") -> List[PriceInfo]:
    """
    Retrieve prices for a specific token in terms of the stable token.

    Args:
        token_address (str): The address of the token to retrieve prices for.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)

    Returns:
        List[Price]: A list of Price objects with token-price mappings.
    """
    token_address = Web3.to_checksum_address(token_address)
    with get_chain(chainId) as chain:
        append_stable = False
        append_native = False

        tokens = [chain.get_token(token_address)]
        if chain.settings.stable_token_addr.lower() != token_address.lower():
            tokens.append(chain.get_token(chain.settings.stable_token_addr))
            append_stable = True

        if chain.settings.native_token_symbol.lower() != token_address.lower():
            tokens.append(
                Token.make_native_token(
                    chain.settings.native_token_symbol,
                    chain.settings.wrapped_native_token_addr,
                    chain.settings.native_token_decimals,
                    chain_id=chain.chain_id,
                    chain_name=chain.name,
                )
            )
            append_native = True

        prices = chain.get_prices(tokens)
        prices = [PriceInfo.from_price(p) for p in prices]
        if append_stable:
            # 如果在获取价格的时候加上了稳定币，在返回结果的时候再从列表里去掉，否则外部应用在传offset的时候会有问题
            prices = [
                p
                for p in prices
                if p.token.token_address.lower()
                != chain.settings.stable_token_addr.lower()
            ]

        if append_native:
            prices = [
                p
                for p in prices
                if p.token.token_address.lower()
                != chain.settings.native_token_symbol.lower()
            ]
        return prices


@mcp.tool()
async def get_prices(
    limit: int, offset: int, listed_only: bool = False, chainId: str = "10"
) -> List[PriceInfo]:
    """
    Retrieve prices for a list of tokens in terms of the stable token.

    Args:
        limit (int): Maximum number of prices to return.
        offset (int): The starting point to retrieve prices.
        listed_only (bool): If True, only return prices for tokens that are marked as 'listed'.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)

    Returns:
        List[Price]: A list of Price objects with token-price mappings.
    """
    with get_chain(chainId) as chain:
        tokens = chain.get_tokens_page(limit, offset)
        tokens = list(
            map(
                lambda t: Token.from_tuple(
                    t, chain_id=chain.chain_id, chain_name=chain.name
                ),
                tokens,
            )
        )

        append_stable = False
        append_native = False

        # 因为get price里需要用到稳定币的价格来计算usd的汇率，这里给tokens里加上一个稳定币
        token_address_list = [t.token_address.lower() for t in tokens]
        if chain.settings.stable_token_addr.lower() not in token_address_list:
            tokens.append(chain.get_token(chain.settings.stable_token_addr))
            append_stable = True

        if chain.settings.native_token_symbol.lower() not in token_address_list:
            tokens.append(
                Token.make_native_token(
                    chain.settings.native_token_symbol,
                    chain.settings.wrapped_native_token_addr,
                    chain.settings.native_token_decimals,
                    chain_id=chain.chain_id,
                    chain_name=chain.name,
                )
            )
            append_native = True

        prices = chain.get_prices(tokens)
        prices = [PriceInfo.from_price(p) for p in prices]
        if append_stable:
            # 如果在获取价格的时候加上了稳定币，在返回结果的时候再从列表里去掉，否则外部应用在传offset的时候会有问题
            prices = [
                p
                for p in prices
                if p.token.token_address.lower()
                != chain.settings.stable_token_addr.lower()
            ]

        if append_native:
            prices = [
                p
                for p in prices
                if p.token.token_address.lower()
                != chain.settings.native_token_symbol.lower()
            ]

        return prices


@mcp.tool()
async def get_pools(limit: int = 30, offset: int = 0, chainId: str = "10", use_cache: bool = True) -> List[LiquidityPoolInfo]:
    """
    Retrieve all raw liquidity pools.

    Args:
        limit (int): The maximum number of pools to retrieve.
        offset (int): The starting point for pagination.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)
        use_cache (bool): Whether to use cached data. Defaults to True.

    Returns:
        List[LiquidityPool] or List[LiquidityPoolForSwap]: A list of pool objects.
    """
    pools = _get_cached_pools(chainId) if use_cache else _get_pools_from_chain(chainId)
    # Apply pagination to cached data
    paginated_pools = pools[offset:offset + limit]
    return [LiquidityPoolInfo.from_pool(p) for p in paginated_pools]
    


@mcp.tool()
async def get_pool_by_address(address: str, chainId: str = "10", use_cache: bool = True) -> LiquidityPoolInfo | None:
    """
    Retrieve a raw liquidity pool by its contract address.

    Args:
        address (str): The address of the liquidity pool contract.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)
        use_cache (bool): Whether to use cached data. Defaults to True.

    Returns:
        Optional[LiquidityPool]: The matching LiquidityPool object, or None if not found.
    """
    address = Web3.to_checksum_address(address)
    pool = _get_pool_from_cache(chainId, address) if use_cache else _get_pool_from_chain(chainId, address)
    return LiquidityPoolInfo.from_pool(pool) if pool else None


@mcp.tool()
async def get_pools_for_swaps(limit: int, offset: int, chainId: str = "10", use_cache: bool = True) -> List[LiquidityPoolForSwapInfo]:
    """
    Retrieve all raw liquidity pools suitable for swaps.

    Args:
        limit (int): The maximum number of pools to retrieve.
        offset (int): The starting point for pagination.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)
        use_cache (bool): Whether to use cached data. Defaults to True.

    Returns:
        List[LiquidityPoolForSwap]: A list of simplified pool objects for swaps.
    """
    # Get pools (either from cache or chain) - returns List[LiquidityPool]
    pools = _get_cached_pools(chainId) if use_cache else _get_pools_from_chain(chainId)
    
    if not pools:
        return []
    
    # Convert LiquidityPool to LiquidityPoolForSwap format
    pools_for_swap = _convert_pools_to_swap_format(pools)
    
    # Apply pagination
    paginated_pools = pools_for_swap[offset:offset + limit]
    
    # Convert to Info objects
    return [LiquidityPoolForSwapInfo.from_pool(p) for p in paginated_pools]


@mcp.tool()
async def get_latest_pool_epochs(offset: int, limit: int = 10, chainId: str = "10") -> List[LiquidityPoolEpochInfo]:
    """
    Retrieve the latest epoch data for all pools.

    Args:
        limit (int): The maximum number of epochs to retrieve.
        offset (int): The starting point for pagination.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)

    Returns:
        List[LiquidityPoolEpoch]: A list of the most recent epochs across all pools.
    """
    with get_chain(chainId) as chain:
        epochs = chain.get_latest_pool_epochs_page(limit, offset)
        return [LiquidityPoolEpochInfo.from_epoch(p) for p in epochs]


@mcp.tool()
async def get_pool_epochs(
    lp: str, offset: int = 0, limit: int = 10, chainId: str = "10"
) -> List[LiquidityPoolEpochInfo]:
    """
    Retrieve historical epoch data for a given liquidity pool.

    Args:
        lp (str): Address of the liquidity pool.
        offset (int): Offset for pagination.
        limit (int): Number of epochs to retrieve.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)

    Returns:
        List[LiquidityPoolEpoch]: A list of epoch entries for the specified pool.
    """
    lp = Web3.to_checksum_address(lp)
    with get_chain(chainId) as chain:
        epochs = chain.get_pool_epochs_page(lp, offset, limit)
        return [LiquidityPoolEpochInfo.from_epoch(p) for p in epochs]


@mcp.tool()
async def get_quote(
    from_token: str,
    to_token: str,
    amount: int,
    chainId: str = "10",
    use_cache: bool = True,
) -> Optional[QuoteInfo]:
    """
    Retrieve the best quote for swapping a given amount from one token to another.

    Args:
        from_token (str): The token to swap from. For OPchain, this can be 'usdc', 'velo', 'eth', or 'o_usdt'. For BaseChain, this can be 'usdc', 'aero', or 'eth'. For Unichain, this can be 'o_usdt' or 'usdc'. For Lisk, this can be 'o_usdt', 'lsk', 'eth', or 'usdt'.
        to_token (str): The token to swap to. For OPchain, this can be 'usdc', 'velo', 'eth', or 'o_usdt'. For BaseChain, this can be 'usdc', 'aero', or 'eth'. For Unichain, this can be 'o_usdt' or 'usdc'. For Lisk, this can be 'o_usdt', 'lsk', 'eth', or 'usdt'.
        amount (int): The amount to swap (unit is wei).
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)
        use_cache (bool): Whether to use cached pool addresses. Defaults to True. When True, uses cached pool addresses to speed up the initial pool lookup, but still gets real-time quotes. When False, fetches pool addresses from chain (slower but ensures latest pool list).

    Returns:
        Optional[Quote]: The best available quote, or None if no valid quote was found.
    """

    if chainId == "10" and (from_token not in ["usdc", "velo", "eth", "o_usdt"] or to_token not in ["usdc", "velo", "eth", "o_usdt"]):
        raise ValueError("Only 'usdc', 'velo', 'eth', and 'o_usdt' are supported on OPChain.")

    if chainId == "130" and (from_token not in ["o_usdt", "usdc"] or to_token not in ["o_usdt", "usdc"]):
        raise ValueError("Only 'o_usdt' and 'usdc' are supported on Unichain.")

    if chainId == "1135" and (from_token not in ["o_usdt", "lsk", "eth", "usdt"] or to_token not in ["o_usdt", "lsk", "eth", "usdt"]):
        raise ValueError("Only 'o_usdt', 'lsk', 'eth', and 'usdt' are supported on List.")

    if chainId == "8453" and (from_token not in ["usdc", "aero", "eth"] or to_token not in ["usdc", "aero", "eth"]):
        raise ValueError("Only 'usdc', 'aero', and 'eth' are supported on BaseChain.")

    with get_chain(chainId) as chain:
        from_token_obj = getattr(chain, from_token, None)
        to_token_obj = getattr(chain, to_token, None)
        if from_token_obj is None or to_token_obj is None:
            raise ValueError("Invalid token specified.")

        # Optimize: Use cached pool addresses if available and use_cache is True
        # This speeds up pool lookup while still getting real-time quotes
        if use_cache:
            cached_pools = _get_cached_pools(chainId)
            if cached_pools:
                try:
                    # Convert cached LiquidityPool to LiquidityPoolForSwap format
                    # This only uses pool addresses from cache, quotes are still real-time
                    pools_for_swap = _convert_pools_to_swap_format(cached_pools)
                    
                    # Temporarily replace get_pools_for_swaps to use cached pools
                    # This optimizes the pool lookup while get_quote still gets real-time liquidity data
                    original_get_pools_for_swaps = chain.get_pools_for_swaps
                    chain.get_pools_for_swaps = lambda: pools_for_swap
                    
                    try:
                        quote = chain.get_quote(from_token_obj, to_token_obj, amount)
                        return QuoteInfo.from_quote(quote) if quote else None
                    finally:
                        # Restore original method
                        chain.get_pools_for_swaps = original_get_pools_for_swaps
                except Exception as e:
                    # If conversion or quote fails, fall back to original method
                    print(f"Warning: Failed to use cached pools, falling back to chain query: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Fallback to original method (use_cache=False or cache miss)
        quote = chain.get_quote(from_token_obj, to_token_obj, amount)
        return QuoteInfo.from_quote(quote) if quote else None

    
@mcp.tool()
async def get_pools_by_token(token_address: str, limit: int = 30, offset: int = 0,  chainId: str = "10", use_cache: bool = True) -> list[LiquidityPoolInfo] | None:
    """
    Retrieve liquidity pools that contain a specific token.

    Args:
        token_address (str): The address of the token to filter pools by.
        limit (int): The maximum number of pools to retrieve.
        offset (int): The starting point for pagination.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)
        use_cache (bool): Whether to use cached data. Defaults to True.

    Returns:
        list[LiquidityPoolInfo] | None: A list of liquidity pool information or None if not found.
    """
    token_address = Web3.to_checksum_address(token_address)
    if not token_address:
        raise ValueError("Token address must be provided.")

    # 1. get all pools from cache or chain
    pools = _get_cached_pools(chainId) if use_cache else _get_pools_from_chain(chainId)
    if not pools:
        return None

    # 2. filter by specific token
    pools = [p for p in pools if p.token0.token_address == token_address or p.token1.token_address == token_address]
    pools = sorted(pools, key=lambda p: p.tvl, reverse=True)
    pools = pools[offset:offset+limit]
    return [LiquidityPoolInfo.from_pool(p) for p in pools]
    

@mcp.tool()
async def get_pools_by_pair(token0_address: str, token1_address: str, limit: int = 30, offset: int = 0, chainId: str = "10", use_cache: bool = True) -> list[LiquidityPoolInfo] | None:
    """
    Retrieve liquidity pools that contain a specific token pair.

    Args:
        token0_address (str): The address of the first token in the pair.
        token1_address (str): The address of the second token in the pair.
        limit (int): The maximum number of pools to retrieve.
        offset (int): The starting point for pagination.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)
        use_cache (bool): Whether to use cached data. Defaults to True.

    Returns:
        list[LiquidityPoolInfo] | None: A list of liquidity pool information or None if not found.
    """
    token0_address = Web3.to_checksum_address(token0_address)
    token1_address = Web3.to_checksum_address(token1_address)
    if not token0_address or not token1_address:
        raise ValueError("Both token addresses must be provided.")

    # 1. get all pools from cache or chain
    pools = _get_cached_pools(chainId) if use_cache else _get_pools_from_chain(chainId)
    if not pools:
        return None

    # 2. filter by specific token pair
    pools = [p for p in pools if (p.token0.token_address == token0_address and p.token1.token_address == token1_address) or (p.token0.token_address == token1_address and p.token1.token_address == token0_address)]
    pools = sorted(pools, key=lambda p: p.tvl, reverse=True)
    pools = pools[offset:offset+limit]
    return [LiquidityPoolInfo.from_pool(p) for p in pools]
    

@mcp.tool()
async def get_pool_list(token_address_list: list[str] = None, pool_type: str = "all",  sort_by: str = "tvl", limit: int = 30, offset: int = 0, chainId: str = "10", use_cache: bool = True) -> list[LiquidityPoolInfo] | None:
    """
    Retrieve liquidity pools based on specified criteria.

    Args:
        token_address_list (list[str] | None): List of token addresses to filter pools, Only One or two tokens are supported for filtering. If None, no token filtering is applied.
        pool_type (str): The type of pools to retrieve ('v2', 'v3' or 'all').
        sort_by (str): The criterion to sort the pools by ('tvl', 'volume', or 'apr').
        limit (int): The maximum number of pools to retrieve.
        offset (int): The starting point for pagination.
        chainId (str): The chain ID to use ('10' for OPChain, '8453' for BaseChain, '130' for Unichain, '1135' for List)
        use_cache (bool): Whether to use cached data. Defaults to True.

    Returns:
        list[LiquidityPoolInfo] | None: A list of liquidity pool information or None if not found.
    """

    @staticmethod
    def safe_get_amount_in_stable(amount_obj, default=0.0):
        # Helper function to safely extract amount_in_stable
        if amount_obj is None:
            return default
        if isinstance(amount_obj, (int, float)):
            return float(amount_obj)
        if hasattr(amount_obj, 'amount_in_stable') and amount_obj.amount_in_stable is not None:
            return amount_obj.amount_in_stable
        return default

    # 1. get all pools from cache or chain
    pools = _get_cached_pools(chainId) if use_cache else _get_pools_from_chain(chainId)
    if not pools:
        return None

    # 2. filter by token_address_list
    if token_address_list is not None:
        if token_address_list and len(token_address_list) == 1:
            token_address = Web3.to_checksum_address(token_address_list[0])
            pools = [p for p in pools if p.token0.token_address == token_address or p.token1.token_address == token_address]
        elif token_address_list and len(token_address_list) == 2:
            token0_address = Web3.to_checksum_address(token_address_list[0])
            token1_address = Web3.to_checksum_address(token_address_list[1])
            pools = [p for p in pools if (p.token0.token_address == token0_address and p.token1.token_address == token1_address) or (p.token0.token_address == token1_address and p.token1.token_address == token0_address)]
        else:
            raise ValueError("Only One or two tokens are supported for filtering.")

    # 3. filter by pool type
    if pool_type not in ["v2", "v3", "all"]:
        raise ValueError("Unsupported pool_type. Use 'v2', 'v3', or 'all'.")
    if pool_type == "v2":
        pools = [p for p in pools if not p.is_cl]
    elif pool_type == "v3":
        pools = [p for p in pools if p.is_cl]

    # 4. sort by given criteria
    if sort_by == "tvl":
        pools.sort(key=lambda p: p.tvl, reverse=True)
    elif sort_by == "volume":
        # fix bug: some pools may have volume as Float or None
        pools.sort(key=lambda p: safe_get_amount_in_stable(p.volume), reverse=True)
    elif sort_by == "apr":
        pools.sort(key=lambda p: p.apr, reverse=True)
    else:
        raise ValueError("Unsupported sort_by criteria. Use 'tvl', 'volume', or 'apr'.")

    pools = pools[offset:offset+limit]
    return [LiquidityPoolInfo.from_pool(p) for p in pools]
 

def main():
    # Check required environment variables
    if not os.environ.get("SUGAR_PK"):
        raise ValueError("Environment variable SUGAR_PK is not set. Please set it to your private key.")

    if not os.environ.get("SUGAR_RPC_URI_8453"):
        raise ValueError("Environment variable SUGAR_RPC_URI_8453 is not set. Please set it to your Base chain RPC URI.")

    print("Starting Sugar MCP server...")

    # Check if we should skip cache initialization (useful for debugging)
    skip_cache_init = os.environ.get("SKIP_CACHE_INIT", "false").lower() == "true"

    if not skip_cache_init:
        # Configure cache settings (visible configuration data)
        cache_config = CacheConfig(
            duration_minutes=30,  # Cache for 30 minutes
            enabled_chain_ids=["8453"],  # Only cache Base chain to reduce memory usage
            filter_invalid_pools=True  # Filter out pools with invalid data
        )

        # Configure and start the cache system
        start_cache_system(cache_config)
    else:
        print("⚠️  Skipping cache initialization (SKIP_CACHE_INIT=true)")
        print("🚀 Server ready! (without cache)")

    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
