"""MCP Server wrapping ib_async for Interactive Brokers API."""

import asyncio
import json
from datetime import datetime, date
from typing import Any
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ib_async import (
    IB, Stock, Option, Future, Forex, Index, CFD, Crypto, Bond,
    Contract, LimitOrder, MarketOrder, StopOrder, StopLimitOrder,
    util
)

# Global IB connection
ib: IB | None = None


def serialize_object(obj: Any) -> Any:
    """Serialize ib_async objects to JSON-compatible format."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (list, tuple)):
        return [serialize_object(item) for item in obj]
    if isinstance(obj, dict):
        return {k: serialize_object(v) for k, v in obj.items()}
    if hasattr(obj, 'dict'):
        return serialize_object(obj.dict())
    if hasattr(obj, '__dict__'):
        return serialize_object(vars(obj))
    return str(obj)


def create_contract(contract_type: str, **kwargs) -> Contract:
    """Create a contract based on type."""
    contract_map = {
        'stock': Stock,
        'option': Option,
        'future': Future,
        'forex': Forex,
        'index': Index,
        'cfd': CFD,
        'crypto': Crypto,
        'bond': Bond,
    }
    contract_class = contract_map.get(contract_type.lower(), Contract)
    return contract_class(**kwargs)


# Create the MCP server
app = Server("ib-async-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        # Connection tools
        Tool(
            name="connect",
            description="Connect to TWS or IB Gateway. Must be called before using other tools.",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "default": "127.0.0.1", "description": "TWS/Gateway host"},
                    "port": {"type": "integer", "default": 7496, "description": "Port (7496 for TWS, 4001 for Gateway)"},
                    "client_id": {"type": "integer", "default": 1, "description": "Client ID"},
                    "readonly": {"type": "boolean", "default": True, "description": "Read-only mode"},
                },
            },
        ),
        Tool(
            name="disconnect",
            description="Disconnect from TWS/Gateway.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="is_connected",
            description="Check if connected to TWS/Gateway.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # Account tools
        Tool(
            name="get_accounts",
            description="Get list of managed account names.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_account_values",
            description="Get account values (balance, margin, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string", "description": "Account ID (optional)"},
                },
            },
        ),
        Tool(
            name="get_account_summary",
            description="Get account summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string", "description": "Account ID (optional)"},
                },
            },
        ),
        Tool(
            name="get_portfolio",
            description="Get portfolio positions with market values.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string", "description": "Account ID (optional)"},
                },
            },
        ),
        Tool(
            name="get_positions",
            description="Get all positions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string", "description": "Account ID (optional)"},
                },
            },
        ),
        Tool(
            name="get_pnl",
            description="Get profit and loss.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string", "description": "Account ID (optional)"},
                },
            },
        ),
        # Contract tools
        Tool(
            name="create_contract",
            description="Create a contract for trading. Types: stock, option, future, forex, index, cfd, crypto, bond.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string", "description": "Contract type"},
                    "symbol": {"type": "string", "description": "Symbol (e.g., AAPL, EURUSD)"},
                    "exchange": {"type": "string", "default": "SMART", "description": "Exchange"},
                    "currency": {"type": "string", "default": "USD", "description": "Currency"},
                    "expiry": {"type": "string", "description": "Expiry date for options/futures (YYYYMMDD)"},
                    "strike": {"type": "number", "description": "Strike price for options"},
                    "right": {"type": "string", "description": "Option right: C (call) or P (put)"},
                    "multiplier": {"type": "string", "description": "Contract multiplier"},
                },
                "required": ["contract_type", "symbol"],
            },
        ),
        Tool(
            name="qualify_contracts",
            description="Qualify contracts to fill in missing fields like conId.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string"},
                    "symbol": {"type": "string"},
                    "exchange": {"type": "string", "default": "SMART"},
                    "currency": {"type": "string", "default": "USD"},
                },
                "required": ["contract_type", "symbol"],
            },
        ),
        Tool(
            name="get_contract_details",
            description="Get detailed contract information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string"},
                    "symbol": {"type": "string"},
                    "exchange": {"type": "string", "default": "SMART"},
                    "currency": {"type": "string", "default": "USD"},
                },
                "required": ["contract_type", "symbol"],
            },
        ),
        Tool(
            name="search_symbols",
            description="Search for matching symbols/contracts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern"},
                },
                "required": ["pattern"],
            },
        ),
        # Market data tools
        Tool(
            name="get_market_data",
            description="Get real-time market data snapshot for a contract.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string"},
                    "symbol": {"type": "string"},
                    "exchange": {"type": "string", "default": "SMART"},
                    "currency": {"type": "string", "default": "USD"},
                },
                "required": ["contract_type", "symbol"],
            },
        ),
        Tool(
            name="get_historical_data",
            description="Get historical bar data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string"},
                    "symbol": {"type": "string"},
                    "exchange": {"type": "string", "default": "SMART"},
                    "currency": {"type": "string", "default": "USD"},
                    "duration": {"type": "string", "default": "1 D", "description": "Duration (e.g., '1 D', '1 W', '1 M', '1 Y')"},
                    "bar_size": {"type": "string", "default": "1 hour", "description": "Bar size (e.g., '1 min', '5 mins', '1 hour', '1 day')"},
                    "what_to_show": {"type": "string", "default": "TRADES", "description": "Data type: TRADES, MIDPOINT, BID, ASK"},
                    "use_rth": {"type": "boolean", "default": True, "description": "Regular trading hours only"},
                },
                "required": ["contract_type", "symbol"],
            },
        ),
        Tool(
            name="get_head_timestamp",
            description="Get earliest available historical data timestamp.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string"},
                    "symbol": {"type": "string"},
                    "exchange": {"type": "string", "default": "SMART"},
                    "currency": {"type": "string", "default": "USD"},
                    "what_to_show": {"type": "string", "default": "TRADES"},
                },
                "required": ["contract_type", "symbol"],
            },
        ),
        # Order tools
        Tool(
            name="place_order",
            description="Place a new order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string"},
                    "symbol": {"type": "string"},
                    "exchange": {"type": "string", "default": "SMART"},
                    "currency": {"type": "string", "default": "USD"},
                    "action": {"type": "string", "description": "BUY or SELL"},
                    "quantity": {"type": "number", "description": "Order quantity"},
                    "order_type": {"type": "string", "description": "Order type: market, limit, stop, stop_limit"},
                    "limit_price": {"type": "number", "description": "Limit price (for limit orders)"},
                    "stop_price": {"type": "number", "description": "Stop price (for stop orders)"},
                },
                "required": ["contract_type", "symbol", "action", "quantity", "order_type"],
            },
        ),
        Tool(
            name="cancel_order",
            description="Cancel an existing order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Order ID to cancel"},
                },
                "required": ["order_id"],
            },
        ),
        Tool(
            name="cancel_all_orders",
            description="Cancel all open orders.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_open_orders",
            description="Get all open orders.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_open_trades",
            description="Get all open trades.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_executions",
            description="Get execution reports.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_fills",
            description="Get order fills.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="what_if_order",
            description="Check margin impact without placing order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_type": {"type": "string"},
                    "symbol": {"type": "string"},
                    "exchange": {"type": "string", "default": "SMART"},
                    "currency": {"type": "string", "default": "USD"},
                    "action": {"type": "string"},
                    "quantity": {"type": "number"},
                    "order_type": {"type": "string", "default": "market"},
                    "limit_price": {"type": "number"},
                },
                "required": ["contract_type", "symbol", "action", "quantity"],
            },
        ),
        # Options tools
        Tool(
            name="get_option_chain",
            description="Get option chain for an underlying.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Underlying symbol"},
                    "exchange": {"type": "string", "default": ""},
                    "underlying_sec_type": {"type": "string", "default": "STK"},
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="calculate_implied_volatility",
            description="Calculate implied volatility from option price.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "expiry": {"type": "string"},
                    "strike": {"type": "number"},
                    "right": {"type": "string"},
                    "option_price": {"type": "number"},
                    "underlying_price": {"type": "number"},
                },
                "required": ["symbol", "expiry", "strike", "right", "option_price", "underlying_price"],
            },
        ),
        Tool(
            name="calculate_option_price",
            description="Calculate option price from volatility.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "expiry": {"type": "string"},
                    "strike": {"type": "number"},
                    "right": {"type": "string"},
                    "volatility": {"type": "number"},
                    "underlying_price": {"type": "number"},
                },
                "required": ["symbol", "expiry", "strike", "right", "volatility", "underlying_price"],
            },
        ),
        # Scanner tools
        Tool(
            name="get_scanner_parameters",
            description="Get available scanner parameters.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="run_scanner",
            description="Run a market scanner.",
            inputSchema={
                "type": "object",
                "properties": {
                    "scan_code": {"type": "string", "description": "Scanner code (e.g., TOP_PERC_GAIN, MOST_ACTIVE)"},
                    "instrument": {"type": "string", "default": "STK", "description": "Instrument type"},
                    "location_code": {"type": "string", "default": "STK.US.MAJOR", "description": "Location code"},
                    "num_rows": {"type": "integer", "default": 10, "description": "Number of results"},
                },
                "required": ["scan_code"],
            },
        ),
        # News tools
        Tool(
            name="get_news_providers",
            description="Get available news providers.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_news_article",
            description="Get a news article.",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider_code": {"type": "string"},
                    "article_id": {"type": "string"},
                },
                "required": ["provider_code", "article_id"],
            },
        ),
        Tool(
            name="get_historical_news",
            description="Get historical news headlines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "con_id": {"type": "integer", "description": "Contract ID"},
                    "provider_codes": {"type": "string", "description": "Comma-separated provider codes"},
                    "total_results": {"type": "integer", "default": 10},
                },
                "required": ["con_id", "provider_codes"],
            },
        ),
        # Utility tools
        Tool(
            name="get_current_time",
            description="Get current TWS server time.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]



@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    global ib
    
    try:
        result = await _handle_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(serialize_object(result), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _handle_tool(name: str, args: dict) -> Any:
    """Route tool calls to appropriate handlers."""
    global ib
    
    # Connection tools
    if name == "connect":
        if ib is not None and ib.isConnected():
            return {"status": "already_connected"}
        ib = IB()
        await ib.connectAsync(
            host=args.get("host", "127.0.0.1"),
            port=args.get("port", 7496),
            clientId=args.get("client_id", 1),
            readonly=args.get("readonly", True),
        )
        return {"status": "connected", "accounts": ib.managedAccounts()}
    
    if name == "disconnect":
        if ib is not None:
            ib.disconnect()
            ib = None
        return {"status": "disconnected"}
    
    if name == "is_connected":
        return {"connected": ib is not None and ib.isConnected()}
    
    # Require connection for other tools
    if ib is None or not ib.isConnected():
        raise RuntimeError("Not connected. Call 'connect' first.")
    
    # Account tools
    if name == "get_accounts":
        return {"accounts": ib.managedAccounts()}
    
    if name == "get_account_values":
        values = ib.accountValues(args.get("account", ""))
        return [{"account": v.account, "tag": v.tag, "value": v.value, "currency": v.currency} for v in values]
    
    if name == "get_account_summary":
        summary = ib.accountSummary(args.get("account", ""))
        return [{"account": v.account, "tag": v.tag, "value": v.value, "currency": v.currency} for v in summary]
    
    if name == "get_portfolio":
        items = ib.portfolio(args.get("account", ""))
        return [{
            "symbol": p.contract.symbol,
            "sec_type": p.contract.secType,
            "position": p.position,
            "market_price": p.marketPrice,
            "market_value": p.marketValue,
            "average_cost": p.averageCost,
            "unrealized_pnl": p.unrealizedPNL,
            "realized_pnl": p.realizedPNL,
            "account": p.account,
        } for p in items]
    
    if name == "get_positions":
        positions = ib.positions(args.get("account", ""))
        return [{
            "account": p.account,
            "symbol": p.contract.symbol,
            "sec_type": p.contract.secType,
            "position": p.position,
            "avg_cost": p.avgCost,
        } for p in positions]
    
    if name == "get_pnl":
        pnl_list = ib.pnl(args.get("account", ""))
        return [{
            "account": p.account,
            "daily_pnl": p.dailyPnL,
            "unrealized_pnl": p.unrealizedPnL,
            "realized_pnl": p.realizedPnL,
        } for p in pnl_list]

    
    # Contract tools
    if name == "create_contract":
        contract_type = args.pop("contract_type")
        kwargs = {k: v for k, v in args.items() if v is not None}
        if "expiry" in kwargs:
            kwargs["lastTradeDateOrContractMonth"] = kwargs.pop("expiry")
        contract = create_contract(contract_type, **kwargs)
        return serialize_object(contract)
    
    if name == "qualify_contracts":
        contract = create_contract(
            args["contract_type"],
            symbol=args["symbol"],
            exchange=args.get("exchange", "SMART"),
            currency=args.get("currency", "USD"),
        )
        qualified = await ib.qualifyContractsAsync(contract)
        return [serialize_object(c) for c in qualified]
    
    if name == "get_contract_details":
        contract = create_contract(
            args["contract_type"],
            symbol=args["symbol"],
            exchange=args.get("exchange", "SMART"),
            currency=args.get("currency", "USD"),
        )
        details = await ib.reqContractDetailsAsync(contract)
        return [serialize_object(d) for d in details]
    
    if name == "search_symbols":
        results = await ib.reqMatchingSymbolsAsync(args["pattern"])
        return [serialize_object(r) for r in (results or [])]
    
    # Market data tools
    if name == "get_market_data":
        contract = create_contract(
            args["contract_type"],
            symbol=args["symbol"],
            exchange=args.get("exchange", "SMART"),
            currency=args.get("currency", "USD"),
        )
        await ib.qualifyContractsAsync(contract)
        tickers = await ib.reqTickersAsync(contract)
        if tickers:
            t = tickers[0]
            return {
                "symbol": contract.symbol,
                "bid": t.bid,
                "ask": t.ask,
                "last": t.last,
                "volume": t.volume,
                "open": t.open,
                "high": t.high,
                "low": t.low,
                "close": t.close,
            }
        return {"error": "No data available"}
    
    if name == "get_historical_data":
        contract = create_contract(
            args["contract_type"],
            symbol=args["symbol"],
            exchange=args.get("exchange", "SMART"),
            currency=args.get("currency", "USD"),
        )
        await ib.qualifyContractsAsync(contract)
        bars = await ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr=args.get("duration", "1 D"),
            barSizeSetting=args.get("bar_size", "1 hour"),
            whatToShow=args.get("what_to_show", "TRADES"),
            useRTH=args.get("use_rth", True),
        )
        return [{
            "date": b.date.isoformat() if hasattr(b.date, 'isoformat') else str(b.date),
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        } for b in bars]
    
    if name == "get_head_timestamp":
        contract = create_contract(
            args["contract_type"],
            symbol=args["symbol"],
            exchange=args.get("exchange", "SMART"),
            currency=args.get("currency", "USD"),
        )
        await ib.qualifyContractsAsync(contract)
        ts = await ib.reqHeadTimeStampAsync(
            contract,
            whatToShow=args.get("what_to_show", "TRADES"),
            useRTH=True,
            formatDate=1,
        )
        return {"head_timestamp": ts.isoformat() if ts else None}

    
    # Order tools
    if name == "place_order":
        contract = create_contract(
            args["contract_type"],
            symbol=args["symbol"],
            exchange=args.get("exchange", "SMART"),
            currency=args.get("currency", "USD"),
        )
        await ib.qualifyContractsAsync(contract)
        
        order_type = args["order_type"].lower()
        action = args["action"].upper()
        quantity = args["quantity"]
        
        if order_type == "market":
            order = MarketOrder(action, quantity)
        elif order_type == "limit":
            order = LimitOrder(action, quantity, args["limit_price"])
        elif order_type == "stop":
            order = StopOrder(action, quantity, args["stop_price"])
        elif order_type == "stop_limit":
            order = StopLimitOrder(action, quantity, args["limit_price"], args["stop_price"])
        else:
            raise ValueError(f"Unknown order type: {order_type}")
        
        trade = ib.placeOrder(contract, order)
        return {
            "order_id": trade.order.orderId,
            "status": trade.orderStatus.status,
            "filled": trade.orderStatus.filled,
            "remaining": trade.orderStatus.remaining,
        }
    
    if name == "cancel_order":
        orders = ib.orders()
        for order in orders:
            if order.orderId == args["order_id"]:
                ib.cancelOrder(order)
                return {"status": "cancel_requested", "order_id": args["order_id"]}
        return {"error": "Order not found"}
    
    if name == "cancel_all_orders":
        ib.reqGlobalCancel()
        return {"status": "cancel_all_requested"}
    
    if name == "get_open_orders":
        orders = ib.openOrders()
        return [serialize_object(o) for o in orders]
    
    if name == "get_open_trades":
        trades = ib.openTrades()
        return [{
            "order_id": t.order.orderId,
            "symbol": t.contract.symbol,
            "action": t.order.action,
            "quantity": t.order.totalQuantity,
            "order_type": t.order.orderType,
            "status": t.orderStatus.status,
            "filled": t.orderStatus.filled,
            "remaining": t.orderStatus.remaining,
        } for t in trades]
    
    if name == "get_executions":
        executions = ib.executions()
        return [serialize_object(e) for e in executions]
    
    if name == "get_fills":
        fills = ib.fills()
        return [{
            "symbol": f.contract.symbol,
            "exec_id": f.execution.execId,
            "side": f.execution.side,
            "shares": f.execution.shares,
            "price": f.execution.price,
            "time": f.time.isoformat() if f.time else None,
            "commission": f.commissionReport.commission if f.commissionReport else None,
        } for f in fills]
    
    if name == "what_if_order":
        contract = create_contract(
            args["contract_type"],
            symbol=args["symbol"],
            exchange=args.get("exchange", "SMART"),
            currency=args.get("currency", "USD"),
        )
        await ib.qualifyContractsAsync(contract)
        
        order_type = args.get("order_type", "market").lower()
        if order_type == "limit":
            order = LimitOrder(args["action"], args["quantity"], args["limit_price"])
        else:
            order = MarketOrder(args["action"], args["quantity"])
        
        state = await ib.whatIfOrderAsync(contract, order)
        return serialize_object(state)

    
    # Options tools
    if name == "get_option_chain":
        contract = Stock(args["symbol"], "SMART", "USD")
        await ib.qualifyContractsAsync(contract)
        chains = await ib.reqSecDefOptParamsAsync(
            args["symbol"],
            args.get("exchange", ""),
            args.get("underlying_sec_type", "STK"),
            contract.conId,
        )
        return [serialize_object(c) for c in chains]
    
    if name == "calculate_implied_volatility":
        contract = Option(
            args["symbol"],
            args["expiry"],
            args["strike"],
            args["right"],
            "SMART",
        )
        await ib.qualifyContractsAsync(contract)
        result = await ib.calculateImpliedVolatilityAsync(
            contract,
            args["option_price"],
            args["underlying_price"],
        )
        return serialize_object(result)
    
    if name == "calculate_option_price":
        contract = Option(
            args["symbol"],
            args["expiry"],
            args["strike"],
            args["right"],
            "SMART",
        )
        await ib.qualifyContractsAsync(contract)
        result = await ib.calculateOptionPriceAsync(
            contract,
            args["volatility"],
            args["underlying_price"],
        )
        return serialize_object(result)
    
    # Scanner tools
    if name == "get_scanner_parameters":
        params = await ib.reqScannerParametersAsync()
        return {"parameters_xml": params[:5000] + "..." if len(params) > 5000 else params}
    
    if name == "run_scanner":
        from ib_async import ScannerSubscription
        subscription = ScannerSubscription(
            scanCode=args["scan_code"],
            instrument=args.get("instrument", "STK"),
            locationCode=args.get("location_code", "STK.US.MAJOR"),
            numberOfRows=args.get("num_rows", 10),
        )
        results = await ib.reqScannerDataAsync(subscription)
        return [{
            "rank": r.rank,
            "symbol": r.contractDetails.contract.symbol if r.contractDetails.contract else None,
            "sec_type": r.contractDetails.contract.secType if r.contractDetails.contract else None,
        } for r in results]
    
    # News tools
    if name == "get_news_providers":
        providers = await ib.reqNewsProvidersAsync()
        return [{"code": p.code, "name": p.name} for p in providers]
    
    if name == "get_news_article":
        article = await ib.reqNewsArticleAsync(args["provider_code"], args["article_id"])
        return {"article_type": article.articleType, "text": article.articleText}
    
    if name == "get_historical_news":
        news = await ib.reqHistoricalNewsAsync(
            args["con_id"],
            args["provider_codes"],
            "",
            "",
            args.get("total_results", 10),
        )
        if news:
            return {
                "time": news.time.isoformat() if news.time else None,
                "provider_code": news.providerCode,
                "article_id": news.articleId,
                "headline": news.headline,
            }
        return {"error": "No news found"}
    
    # Utility tools
    if name == "get_current_time":
        time = await ib.reqCurrentTimeAsync()
        return {"server_time": time.isoformat()}
    
    raise ValueError(f"Unknown tool: {name}")


async def main_async():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    """Entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
