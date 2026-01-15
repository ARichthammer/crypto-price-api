from fastapi import FastAPI, HTTPException
import requests

app = FastAPI(
    title="Crypto Price Service",
    description="Agent-friendly crypto price lookup service using CoinGecko",
    version="1.0.0"
)

# --- Coin alias mapping (Top Coins) ---
COIN_ALIASES = {
    "bitcoin": ["bitcoin", "btc"],
    "ethereum": ["ethereum", "eth"],
    "solana": ["solana", "sol"],
    "ripple": ["ripple", "xrp"],
    "cardano": ["cardano", "ada"],
    "dogecoin": ["dogecoin", "doge"],
    "polkadot": ["polkadot", "dot"],
    "litecoin": ["litecoin", "ltc"],
    "chainlink": ["chainlink", "link"],
    "polygon": ["polygon", "matic"]
}


def resolve_coin_id(user_input: str):
    normalized = user_input.lower().strip()
    for coin_id, aliases in COIN_ALIASES.items():
        if normalized in aliases:
            return coin_id
    return None


@app.get(
    "/crypto/price",
    summary="Get current crypto price in USD",
    description=(
        "Returns the current USD price of a cryptocurrency.\n\n"
        "Accepts natural language names or symbols (e.g. 'Bitcoin', 'BTC', 'Ethereum', 'ETH').\n"
        "Internally resolves them to CoinGecko coin IDs.\n\n"
        "If the coin cannot be resolved, the response contains actionable guidance."
    ),
)
def get_crypto_price(coin: str):
    """
    Agentic design notes:
    - Accepts natural language input
    - Normalizes internally
    - Returns actionable error objects instead of hard failures
    """

    coin_id = resolve_coin_id(coin)

    if not coin_id:
        return {
            "error": {
                "code": "UNKNOWN_CRYPTO",
                "message": f"Unable to resolve crypto identifier '{coin}'.",
                "cause": "The pricing API requires a CoinGecko coin ID.",
                "suggestions": [
                    "Ask the user to clarify the cryptocurrency name",
                    "Use common names like 'bitcoin' or 'ethereum'",
                    "Supported examples: bitcoin/BTC, ethereum/ETH, solana/SOL, cardano/ADA"
                ],
                "supported_coins": list(COIN_ALIASES.keys()),
                "example_fix": "bitcoin"
            }
        }

    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        return {
            "coin_id": coin_id,
            "currency": "USD",
            "price": data[coin_id]["usd"],
            "note": "Price resolved successfully using normalized coin identifier."
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "COINGECKO_API_ERROR",
                    "message": "Failed to retrieve price from CoinGecko.",
                    "cause": str(e),
                    "suggestions": [
                        "Retry later",
                        "Check CoinGecko API availability"
                    ]
                }
            }
        )
