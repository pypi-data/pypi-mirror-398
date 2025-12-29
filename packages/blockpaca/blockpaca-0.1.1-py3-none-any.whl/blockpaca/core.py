import time
import json
import asyncio
import aiohttp
import numpy as np
import polars as pl
from functools import partial
from multiprocessing import shared_memory, Process, Queue, BoundedSemaphore, Event, cpu_count
import websocket
import zmq
from typing import Any 
from .tools import trade_update_to_csv 
import os 
import uuid 


USE_ALPACA = True 

def get_trading_stream():
    from alpaca.trading.stream import TradingStream
    return TradingStream


from .tools import get_socket, convert_run_duration_to_seconds
ALPACA_STREAM_URL = get_socket()

ALPACA_REST_BASE = "https://paper-api.alpaca.markets/v2"


def make_alpaca_headers(api_key: str, secret_key: str) -> dict:
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "Content-Type": "application/json",
    }


def on_open(ws, tickers, api_key, secret_key):

    auth_data = {"action": "auth", "key": api_key, "secret": secret_key}
    ws.send(json.dumps(auth_data))
    listen_msg = {"action": "subscribe", "quotes": tickers}
    ws.send(json.dumps(listen_msg))


def run_quote_stream(shm_meta, tickers, result_q, api_key, secret_key):
    ws = websocket.WebSocketApp(
        ALPACA_STREAM_URL,
        on_open=partial(on_open, tickers=tickers, api_key=api_key, secret_key=secret_key),
        on_message=partial(on_message, shm_meta, result_q),
    )
    ws.run_forever() 


def on_message(shm_meta, result_q, ws, message):
    try:
        data = json.loads(message)
    except Exception as e:
        print("JSON parse error:", e)
        return
    for event in data:
        if event.get("T") == "q":
            write_quote_shm(shm_meta, event)
            result_q.put({
                "type": "quote",
                "ticker": event.get("S"),
                "bid": float(event.get("bp", 0.0)),
                "ask": float(event.get("ap", 0.0)),
            }) 


class QuoteStream:
    def __init__(self, shm_meta, tickers, result_q, api_key, secret_key):
        self.shm_meta = shm_meta
        self.tickers = tickers
        self.result_q = result_q
        self.api_key = api_key
        self.secret_key = secret_key
        self.proc = None

    def __enter__(self):
        self.proc = Process(
            target=run_quote_stream,
            args=(self.shm_meta, self.tickers, self.result_q, self.api_key, self.secret_key)
        )
        self.proc.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc.join()



class PriceSharedMemory:
    def __init__(self, ticker_list):
        self.tickers = ticker_list
        self.n = len(ticker_list)
        self.bids_shm = shared_memory.SharedMemory(create=True, size=self.n * 8)
        self.asks_shm = shared_memory.SharedMemory(create=True, size=self.n * 8)
        self.bids = np.ndarray((self.n,), dtype=np.float64, buffer=self.bids_shm.buf)
        self.asks = np.ndarray((self.n,), dtype=np.float64, buffer=self.asks_shm.buf)
        self.bids[:] = 0.0; self.asks[:] = 0.0
        self.ticker_index = {t: i for i, t in enumerate(ticker_list)}

    def meta(self):
        return {
            "bids_shm_name": self.bids_shm.name,
            "asks_shm_name": self.asks_shm.name,
            "ticker_index": self.ticker_index,
            "n": self.n,
        }

    def close(self):
        try:
            self.bids_shm.close(); self.bids_shm.unlink()
        except Exception:
            pass
        try:
            self.asks_shm.close(); self.asks_shm.unlink()
        except Exception:
            pass

    def __enter__(self): return self 

    def __exit__(self, exc_type, exc, tb): self.close() 


def write_quote_shm(shm_meta, quote):
    bids_shm = shared_memory.SharedMemory(name=shm_meta['bids_shm_name'])
    asks_shm = shared_memory.SharedMemory(name=shm_meta['asks_shm_name'])
    bids = np.ndarray((shm_meta['n'],), dtype=np.float64, buffer=bids_shm.buf)
    asks = np.ndarray((shm_meta['n'],), dtype=np.float64, buffer=asks_shm.buf)
    idx = shm_meta['ticker_index'].get(quote.get("S"))
    if idx is not None:
        if "bp" in quote: bids[idx] = float(quote["bp"])
        if "ap" in quote: asks[idx] = float(quote["ap"])
    bids_shm.close(); asks_shm.close()


class Single_Owner_Portfolio:
    def __init__(self, name: str, method: str, available_capital: float):
        self.positions: pl.DataFrame | None = None
        self.signals: pl.DataFrame | None = None
        self.name = name
        self.method = method
        self.available_capital = float(available_capital)
        self.gross_capital = float(available_capital)
        self.realized_profit = 0.0 


    def apply_buy_execution(self, ticker: str, qty: float, px: float) -> None:
        qty = float(qty); px = float(px)
        if self.positions is None or self.positions.is_empty():
            self.positions = pl.DataFrame({
                'ticker': [ticker],
                'quantity': [qty],
                'bought_at': [px],
                'cost_basis': [qty * px],
                'pos_val': [qty * px],
                'bid': [0.0],
                'ask': [0.0],
            })
        else:
            exists = not self.positions.filter(pl.col('ticker') == ticker).is_empty()
            if not exists:
                add = pl.DataFrame({
                    'ticker': [ticker],
                    'quantity': [qty],
                    'bought_at': [px],
                    'cost_basis': [qty * px],
                    'pos_val': [qty * px],
                    'bid': [0.0],
                    'ask': [0.0],
                })
                self.positions = pl.concat([self.positions, add], how='vertical')
            else:
                row = self.positions.filter(pl.col('ticker') == ticker).select('quantity', 'bought_at').row(0)
                old_q, old_cb = float(row[0]), float(row[1])
                new_q = old_q + qty
                new_cb = (old_q * old_cb + qty * px) / new_q if new_q != 0 else 0.0
                new_cost_basis = new_q * new_cb
                self.positions = self.positions.with_columns(
                    pl.when(pl.col('ticker') == ticker).then(new_q).otherwise(pl.col('quantity')).alias('quantity'),
                    pl.when(pl.col('ticker') == ticker).then(new_cb).otherwise(pl.col('bought_at')).alias('bought_at'),
                    pl.when(pl.col('ticker') == ticker).then(new_cost_basis).otherwise(pl.col('cost_basis')).alias('cost_basis'),
                    pl.when(pl.col('ticker') == ticker).then(new_q * new_cb).otherwise(pl.col('pos_val')).alias('pos_val'),
                )
        self.available_capital -= qty * px 


    def apply_sell_execution(self, ticker: str, qty: float, px: float) -> None:
        if self.positions is None or self.positions.is_empty():
            return
        pos = self.positions.filter(pl.col('ticker') == ticker)
        if pos.is_empty():
            return

        qty = float(qty); px = float(px)
        row = pos.select('quantity', 'bought_at').row(0)
        old_q, cb = float(row[0]), float(row[1])

        if old_q > 0:
            sell_q = min(qty, old_q)
            realized = (px - cb) * sell_q
            self.realized_profit += realized
            self.available_capital += sell_q * px
            new_q = old_q - sell_q
        elif old_q < 0:
            cover_q = min(abs(qty), abs(old_q))
            realized = (cb - px) * cover_q
            self.realized_profit += realized
            self.available_capital += cover_q * (cb - px)
            new_q = old_q + cover_q
        else:
            return

        if new_q == 0:
            self.positions = self.positions.filter(pl.col('ticker') != ticker)
        else:
            new_cost_basis = new_q * cb
            self.positions = self.positions.with_columns(
                pl.when(pl.col('ticker') == ticker).then(new_q).otherwise(pl.col('quantity')).alias('quantity'),
                pl.when(pl.col('ticker') == ticker).then(new_cost_basis).otherwise(pl.col('cost_basis')).alias('cost_basis'),
                pl.when(pl.col('ticker') == ticker).then(new_q * cb).otherwise(pl.col('pos_val')).alias('pos_val'),
            ) 


    def update_quotes(self, ticker: str, bid: float, ask: float):
        if self.positions is None or self.positions.is_empty():
            return
        if self.positions.filter(pl.col("ticker") == ticker).is_empty():
            return
        self.positions = self.positions.with_columns(
            pl.when(pl.col("ticker") == ticker).then(bid).otherwise(pl.col("bid")).alias("bid"),
            pl.when(pl.col("ticker") == ticker).then(ask).otherwise(pl.col("ask")).alias("ask"),
        ) 


    def calc_unrealized_pnl(self) -> float:
        if self.positions is None or self.positions.is_empty():
            return 0.0
        def pnl(row):
            qty, cb, bid, ask = row[1], row[2], row[3], row[4]
            mid = (bid + ask) / 2 if (bid > 0 and ask > 0) else cb
            return (mid - cb) * qty if qty > 0 else (cb - mid) * abs(qty)
        return sum([pnl(r) for r in self.positions.select("ticker","quantity","bought_at","bid","ask").iter_rows()])
    

    def total_pnl(self) -> float:
        return self.realized_profit + self.calc_unrealized_pnl()
    

    def summary(self) -> pl.DataFrame:
        if self.positions is None or self.positions.is_empty():
            return pl.DataFrame()
        rows = []
        for row in self.positions.iter_rows(named=True):
            qty, cb, bid, ask = row["quantity"], row["bought_at"], row["bid"], row["ask"]
            mid = (bid + ask) / 2 if (bid > 0 and ask > 0) else cb
            unrealized = (mid - cb) * qty if qty > 0 else (cb - mid) * abs(qty)
            rows.append({
                "Asset": row["ticker"],
                "Qty": qty,
                "Cost Basis": cb * qty,
                "Last Px": mid,
                "Market Value": qty * mid,
                "Unrealized P&L": unrealized,
                "% Change (All Time)": (unrealized / (cb * abs(qty))) * 100 if cb != 0 else 0.0,
            })
        df = pl.DataFrame(rows)
        totals = {
            "Asset": "TOTAL",
            "Qty": df["Qty"].sum(),
            "Cost Basis": df["Cost Basis"].sum(),
            "Last Px": None,
            "Market Value": df["Market Value"].sum(),
            "Unrealized P&L": df["Unrealized P&L"].sum(),
            "% Change (All Time)": (
                (df["Unrealized P&L"].sum() / df["Cost Basis"].sum()) * 100
                if df["Cost Basis"].sum() != 0 else 0.0
            ),
        }
        return pl.concat([df, pl.DataFrame([totals])], how="vertical")
    
    def summary_as_dicts(self) -> list[dict]:
        """Return summary as list of dicts for the live display."""
        if self.positions is None or self.positions.is_empty():
            return []
        rows = []
        for row in self.positions.iter_rows(named=True):
            qty, cb, bid, ask = row["quantity"], row["bought_at"], row["bid"], row["ask"]
            mid = (bid + ask) / 2 if (bid > 0 and ask > 0) else cb
            unrealized = (mid - cb) * qty if qty > 0 else (cb - mid) * abs(qty)
            rows.append({
                "Asset": row["ticker"],
                "Qty": qty,
                "Cost Basis": cb * qty,
                "Last Px": mid,
                "Market Value": qty * mid,
                "Unrealized P&L": unrealized,
                "% Change (All Time)": (unrealized / (cb * abs(qty))) * 100 if cb != 0 else 0.0,
            })
        
        if rows:
            total_cost = sum(r["Cost Basis"] for r in rows)
            total_value = sum(r["Market Value"] for r in rows)
            total_pnl = sum(r["Unrealized P&L"] for r in rows)
            rows.append({
                "Asset": "TOTAL",
                "Qty": sum(r["Qty"] for r in rows[:-1]) if len(rows) > 1 else rows[0]["Qty"],
                "Cost Basis": total_cost,
                "Last Px": None,
                "Market Value": total_value,
                "Unrealized P&L": total_pnl,
                "% Change (All Time)": (total_pnl / total_cost * 100) if total_cost != 0 else 0.0,
            })
        
        return rows


async def _send_single_order_aio(session, order, result_queue, worker_id, tokens_sem: Any, alpaca_headers: dict, max_retries=3):
    await asyncio.to_thread(tokens_sem.acquire)
    cid = f"{order.get('action','order')}-{worker_id}-{uuid.uuid4().hex[:8]}"
    body = {
        "symbol": order["ticker"],
        "qty": str(order["quantity"]),
        "side": "buy" if order["side"] == "buy" else "sell",
        "type": "market" if order["order_type"] == "market" else "limit",
        "time_in_force": "day",
        "client_order_id": cid,
    }
    if order.get("order_type") != "market" and order.get("limit_price") is not None:
        body["limit_price"] = str(order.get("limit_price")) 

    backoff = 0.5
    for attempt in range(1, max_retries + 1):
        try:
            async with session.post(f"{ALPACA_REST_BASE}/orders", json=body, headers=alpaca_headers, timeout=15) as resp:
                status = resp.status
                data = await resp.json()
                result_queue.put({
                    "type": "submitted",
                    "client_order_id": cid,
                    "order": order,
                    "status_code": status,
                    "resp": data,
                    "worker_id": worker_id,
                    "timestamp": time.time()
                })
                return
        except Exception as e:
            if attempt == max_retries:
                result_queue.put({"status": "error", "reason": repr(e), "order": order, "worker_id": worker_id})
                return
            await asyncio.sleep(backoff)
            backoff *= 2


async def _submit_orders_aio(orders, result_queue, worker_id, tokens_sem: Any, alpaca_headers: dict, concurrency=100):
    conn = aiohttp.TCPConnector(limit=concurrency)
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        tasks = [_send_single_order_aio(session, o, result_queue, worker_id, tokens_sem, alpaca_headers) for o in orders]
        await asyncio.gather(*tasks)


def execution_worker_zmq(pull_endpoint, result_queue, shm_meta, worker_id: int, tokens_sem: Any, api_key: str, secret_key: str, use_alpaca: bool):

    
    alpaca_headers = make_alpaca_headers(api_key, secret_key)
    
    bids_shm = shared_memory.SharedMemory(name=shm_meta['bids_shm_name'])
    asks_shm = shared_memory.SharedMemory(name=shm_meta['asks_shm_name'])

    bids = np.ndarray((shm_meta['n'],), dtype=np.float64, buffer=bids_shm.buf)
    asks = np.ndarray((shm_meta['n'],), dtype=np.float64, buffer=asks_shm.buf)

    ctx = zmq.Context()
    pull = ctx.socket(zmq.PULL)
    pull.connect(pull_endpoint)

    try:
        while True:
            msg = pull.recv_json()
            if msg is None:
                continue
            if msg.get("type") == "shutdown":
                break
            orders = msg["orders"] if msg.get("type") == "batch" and "orders" in msg else [msg]

            if not use_alpaca:
                for order in orders:
                    ticker = order["ticker"]
                    idx = shm_meta['ticker_index'].get(ticker)
                    if idx is None: continue
                    bid, ask = float(bids[idx]), float(asks[idx])
                    px = ask if order["side"] == "buy" else bid
                    result_queue.put({
                        "type": "execution", "order": order,
                        "side": order["side"], "action": order.get("action"),
                        "ticker": ticker, "executed_price": px,
                        "executed_qty": float(order["quantity"]), "status": "filled",
                        "worker_id": worker_id, "timestamp": time.time()
                    })
                continue

            asyncio.run(_submit_orders_aio(orders, result_queue, worker_id, tokens_sem, alpaca_headers, concurrency=100))

    finally:
        bids_shm.close(); asks_shm.close()
        pull.close(); ctx.term()


def trade_update_listener(result_queue, log_name, log_path, api_key: str, secret_key: str, display_queue: Queue = None):

    TradingStream = get_trading_stream()
    stream = TradingStream(api_key, secret_key, paper=True)
    path = f"{log_path}/{log_name}.csv"

    async def on_update(data):
        o = data.order
        status_raw = str(o.status)
        status = status_raw.split(".")[-1].lower()
        cid = o.client_order_id or ""
        action = cid.split("-")[0] if cid else "unknown"
        msg = {
            "type": "execution",
            "client_order_id": cid,
            "ticker": o.symbol,
            "executed_price": float(o.filled_avg_price or 0.0),
            "executed_qty": float(o.filled_qty or 0.0),
            "status": status,
            "side": str(o.side).split(".")[-1].lower(),
            "action": action,
            "timestamp": time.time(),
            "raw_status": status_raw
        }
        result_queue.put(msg)
        
        # Send to display if available
        if display_queue is not None:
            display_queue.put({
                "type": "trade",
                "data": msg
            })
        
        # print("Trade update:", msg)
        trade_update_to_csv(path, msg)

    stream.subscribe_trade_updates(on_update)
    stream.run()


def portfolio_owner(cmd_q, result_q, initial_tickers: list[str], display_queue: Queue = None, use_print: bool = True):
    pf = Single_Owner_Portfolio("owner", "paper", 100_000)
    last_cum_qty: dict[str, float] = {}
    last_print = time.time()
    last_display_update = time.time()

    if initial_tickers:
        pf.signals = pl.DataFrame({
            "ticker": initial_tickers,
            "bid": [0.0] * len(initial_tickers),
            "ask": [0.0] * len(initial_tickers),
            "volume": [0.0] * len(initial_tickers),
        })

    running = True
    while running:
        try:
            msg = result_q.get(timeout=0.05)
        except Exception:
            msg = None

        if msg:
            mtype = msg.get("type")
            if mtype == "quote":
                ticker = msg.get("ticker")
                if ticker:
                    bid = float(msg.get("bid") or 0.0)
                    ask = float(msg.get("ask") or 0.0)
                    pf.update_quotes(ticker, bid, ask)
            elif mtype == "execution":
                if "order" in msg and "client_order_id" not in msg:
                    order = msg["order"]
                    ticker = msg["ticker"]
                    px = float(msg.get("executed_price") or 0.0)
                    qty = float(msg.get("executed_qty") or 0.0)
                    side = order.get("side")
                    action = order.get("action", "sell_long")
                    if side == "buy":
                        if action == "buy_to_cover":
                            pf.apply_sell_execution(ticker, -qty, px)
                        else:
                            pf.apply_buy_execution(ticker, qty, px)
                    elif side == "sell":
                        if action == "short_sell":
                            pf.apply_buy_execution(ticker, -qty, px)
                        else:
                            pf.apply_sell_execution(ticker, qty, px)
                else:
                    cid = msg.get("client_order_id")
                    if cid:
                        prev = float(last_cum_qty.get(cid, 0.0))
                        cum_qty = float(msg.get("executed_qty") or 0.0)
                        delta = cum_qty - prev
                        if delta > 0.0:
                            last_cum_qty[cid] = cum_qty
                            ticker = msg["ticker"]
                            px = float(msg.get("executed_price") or 0.0)
                            side = (msg.get("side") or "").lower()
                            action = msg.get("action")
                            if side == "buy":
                                if action == "buy_to_cover":
                                    pf.apply_sell_execution(ticker, -delta, px)
                                else:
                                    pf.apply_buy_execution(ticker, delta, px)
                            elif side == "sell":
                                if action == "short_sell":
                                    pf.apply_buy_execution(ticker, -delta, px)
                                else:
                                    pf.apply_sell_execution(ticker, delta, px)

        if display_queue is not None and time.time() - last_display_update > 0.5:
            display_queue.put({
                "type": "portfolio",
                "data": pf.summary_as_dicts(),
                "realized_pnl": pf.realized_profit,
                "available_capital": pf.available_capital,
            })
            last_display_update = time.time()

        # Print to console every 5 seconds (only if display is off)
        if use_print and time.time() - last_print > 5:
            print("==== Portfolio Snapshot ====")
            print(pf.summary())
            print(f"Realized P&L: {pf.realized_profit:.2f}")
            print("============================")
            last_print = time.time()

        try:
            cmd = cmd_q.get_nowait()
            if cmd.get("type") == "shutdown":
                running = False
            elif cmd.get("type") == "get_positions":
                if pf.positions is not None and not pf.positions.is_empty():
                    result_q.put({
                        "type": "positions_snapshot",
                        "positions": pf.positions.to_dicts(),
                        "timestamp": time.time()
                    })
                else:
                    result_q.put({"type": "positions_snapshot", "positions": [], "timestamp": time.time()})
        except Exception:
            pass


def get_current_quotes(shm_meta, tickers: list[str] | None = None, as_polars: bool = True):
    bids_shm = shared_memory.SharedMemory(name=shm_meta['bids_shm_name'])
    asks_shm = shared_memory.SharedMemory(name=shm_meta['asks_shm_name'])
    n = shm_meta['n']
    bids = np.ndarray((n,), dtype=np.float64, buffer=bids_shm.buf)
    asks = np.ndarray((n,), dtype=np.float64, buffer=asks_shm.buf)
    ticker_index = shm_meta['ticker_index']
    try:
        if tickers is None:
            tickers = list(ticker_index.keys())
        else:
            tickers = [t for t in tickers if t in ticker_index]
        data = []
        for t in tickers:
            i = ticker_index[t]
            data.append((t, float(bids[i]), float(asks[i])))
        if as_polars:
            df = pl.DataFrame(data, schema=["ticker", "bid", "ask"])
            return df
        else:
            return {t: {"bid": float(bids[ticker_index[t]]), "ask": float(asks[ticker_index[t]])} for t in tickers}
    finally:
        bids_shm.close(); asks_shm.close()


class Trading_Algorithm:
    def __init__(self, shm_meta, cmd_queue, result_queue, order_endpoint: str, num_workers: int = 2, trading_algo=None, frequency=1.0):
        self.shared_memory = shm_meta
        self.command_queue = cmd_queue
        self.result_queue = result_queue
        self.trading_algo = trading_algo
        self.frequency = convert_run_duration_to_seconds(frequency) if isinstance(frequency, str) else frequency
        self.order_endpoint = order_endpoint
        self.num_workers = num_workers
        self.tickers = None
        self.zctx = zmq.Context()
        self.push = self.zctx.socket(zmq.PUSH)
        self.push.connect(order_endpoint) 


    def get_current_data(self):
        self.command_queue.put({"type": "get_positions"})
        positions = None
        try:
            msg = self.result_queue.get(timeout=1.0)
            if msg.get("type") == "positions_snapshot":
                positions = msg.get("positions", [])
        except Exception:
            print("FAILED TO RETRIEVE PORTFOLIO POSITIONS")
        quotes = get_current_quotes(self.shared_memory, as_polars=False)
        if not quotes or all(q["bid"] == 0.0 and q["ask"] == 0.0 for q in quotes.values()):
            print("WARNING: Quote data unavailable or empty.")
            return None, positions
        return quotes, positions 

    def submit_order(self, payload, test_mode=False):

        submission_time = time.time()
        if isinstance(payload, list):
            chunk_size = max(1, len(payload) // self.num_workers)
            batches = [payload[i:i + chunk_size] for i in range(0, len(payload), chunk_size)]
            for batch in batches:
                if batch:
                    self.push.send_json({"type": "batch", "orders": batch})
        elif isinstance(payload, dict):
            self.push.send_json(payload)

    def run_strategy(self):
        while True:
            quotes, positions = self.get_current_data()
            if positions is None:
                positions = []
            if quotes is None:
                time.sleep(self.frequency)
                continue

            orders = self.trading_algo(quotes, positions)
            self.submit_order(orders)
            time.sleep(self.frequency)


def rate_replenisher(tokens_sem: Any, refill_interval_sec: int, stop_event: Any):
    try:
        while not stop_event.is_set():
            time.sleep(refill_interval_sec)
            while True:
                try:
                    tokens_sem.release()
                except ValueError:
                    break
    except KeyboardInterrupt:
        pass 


def run_trading(strategy_callable,
                trade_log_name: str,
                trade_log_path: str,
                api_key: str,
                secret_key: str,
                tickers,
                frequency: float,
                run_seconds: float,
                total_allowed_per_min: int = 190,
                refill_interval_sec: int = 60,
                num_workers: int | None = None,
                use_alpaca: bool = True,
                eos_behavior: str = "liquidate",
                custom_shutdown_action=None,
                warm_up_period=10,
                live_display: bool = False,
                display_refresh_rate: float = 0.5,
                max_trade_updates: int = 15):
    """
    Run a trading strategy.
    
    Args:
        strategy_callable: The strategy function to execute
        trade_log_name: Name for the trade log file
        trade_log_path: Directory path for trade logs
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        tickers: List of tickers to trade
        frequency: How often to run the strategy (seconds)
        run_seconds: Total runtime in seconds
        total_allowed_per_min: Rate limit for orders per minute
        refill_interval_sec: How often to refill rate limit tokens
        num_workers: Number of execution workers (None for auto)
        use_alpaca: Whether to use Alpaca API or simulate
        eos_behavior: End-of-session behavior ("liquidate", "hold", "custom")
        custom_shutdown_action: Custom function for eos_behavior="custom"
        warm_up_period: Seconds to wait for quotes before starting
        live_display: Enable rich live display (uses additional process)
        display_refresh_rate: How often to refresh the display (seconds)
        max_trade_updates: Max trade updates to show in display
    
    Returns:
        dict: Process references
    """

    result_q, cmd_q = Queue(), Queue()
    display_q = Queue() if live_display else None

    tokens_sem = BoundedSemaphore(total_allowed_per_min)
    stop_replenisher = Event()
    replenisher = None

    total_cores = cpu_count() or 1
    reserved = 3 + (1 if use_alpaca else 0) + (1 if live_display else 0)

    if num_workers is None:
        num_workers = max(1, total_cores - reserved)

    procs = {"workers": []}
    display_proc = None

    with PriceSharedMemory(tickers) as shm:
        shm_meta = shm.meta()

        # Start live display if enabled
        if live_display:
            from .live_display import live_display_worker
            display_proc = Process(
                target=live_display_worker,
                args=(display_q, display_refresh_rate, max_trade_updates),
                daemon=True
            )
            display_proc.start()
            procs["display"] = display_proc
            display_q.put({"type": "status", "data": "Initializing..."})

        quote_stream = QuoteStream(shm_meta, tickers, result_q, api_key, secret_key)
        quote_stream.__enter__()
        procs["quote_stream"] = quote_stream

        owner = Process(
            target=portfolio_owner, 
            args=(cmd_q, result_q, tickers, display_q, not live_display)
        )
        owner.start()
        procs["owner"] = owner

        replenisher = Process(target=rate_replenisher, args=(tokens_sem, refill_interval_sec, stop_replenisher))
        replenisher.start()
        procs["replenisher"] = replenisher

        listener = None
        if use_alpaca:
            listener = Process(
                target=trade_update_listener, 
                args=(result_q, trade_log_name, trade_log_path, api_key, secret_key, display_q)
            )
            listener.start()
            procs["listener"] = listener

        
        zmq_ctx = zmq.Context()
        push = zmq_ctx.socket(zmq.PUSH)
        push.bind("tcp://127.0.0.1:*")
        zmq_endpoint = push.getsockopt_string(zmq.LAST_ENDPOINT)


        if not live_display:
            pass 
        procs["push"] = push
        procs["zmq_ctx"] = zmq_ctx

        workers = []
        for wid in range(num_workers):
            p = Process(
                target=execution_worker_zmq, 
                args=(zmq_endpoint, result_q, shm_meta, wid, tokens_sem, api_key, secret_key, use_alpaca)
            )
            p.start()
            if not live_display:
                pass 
            workers.append(p)
        procs["workers"] = workers

        time.sleep(1.5)
        if not live_display:
            for p in workers:
                pass

        algo = Trading_Algorithm(
            shm_meta, cmd_q, result_q, zmq_endpoint, 
            num_workers=num_workers, trading_algo=strategy_callable, frequency=frequency
        )
        algo.push = push 
        algo.order_endpoint = zmq_endpoint
        
        if live_display:
            display_q.put({"type": "status", "data": f"Warming up ({warm_up_period}s)..."})
        
        time.sleep(warm_up_period)

        start = time.time()
        try:
            while True:
                elapsed = time.time() - start
                if elapsed >= run_seconds:
                    break
                
                if live_display:
                    remaining = run_seconds - elapsed
                    display_q.put({"type": "status", "data": f"Running... {remaining:.0f}s remaining"})
                
                context = {
                    "get_current_data": algo.get_current_data,
                    "submit_order": algo.submit_order,
                    "shm_meta": shm_meta,
                    "result_queue": result_q,
                    "command_queue": cmd_q,
                }
                try:
                    orders = strategy_callable(context)
                    if orders:
                        algo.submit_order(orders)
                except Exception:
                    pass
                time.sleep(frequency)

        finally:
            if live_display:
                display_q.put({"type": "status", "data": "Shutting down..."})
            
            if eos_behavior == "liquidate":
                if not live_display:
                    print("Liquidating all positions...")
                quotes, positions = algo.get_current_data()
                if positions:
                    liquidation_orders = []
                    for pos in positions:
                        ticker = pos["ticker"]
                        quantity = pos["quantity"]

                        if quantity > 0:
                            liquidation_orders.append({
                                "side": "sell",
                                "action": "liquidate",
                                "order_type": "market",
                                "ticker": ticker,
                                "quantity": quantity
                            })
                        elif quantity < 0:
                            liquidation_orders.append({
                                "side": "buy",
                                "action": "cover_short",
                                "order_type": "market",
                                "ticker": ticker,
                                "quantity": abs(quantity)
                            })
                    algo.submit_order(liquidation_orders)
            elif eos_behavior == "custom" and callable(custom_shutdown_action):
                if not live_display:
                    print("Executing custom shutdown action...")
                context = {
                    "get_current_data": algo.get_current_data,
                    "submit_order": algo.submit_order,
                    "shm_meta": shm_meta,
                    "result_queue": result_q,
                    "command_queue": cmd_q,
                }
                custom_shutdown_orders = custom_shutdown_action(context)
                if custom_shutdown_orders:
                    algo.submit_order(custom_shutdown_orders)
            elif eos_behavior == "hold":
                if not live_display:
                    print("Holding all positions...")

            for _ in workers:
                push.send_json({"type": "shutdown"})
            for p in workers:
                p.join(timeout=5)

            try:
                push.close()
                zmq_ctx.term()
            except Exception:
                pass

            cmd_q.put({"type": "shutdown"})
            owner.join(timeout=5)

            if listener:
                try:
                    listener.terminate()
                    listener.join(timeout=5)
                except Exception:
                    pass

            try:
                quote_stream.__exit__(None, None, None)
            except Exception:
                pass

            stop_replenisher.set()
            if replenisher:
                replenisher.join(timeout=5)
            
            if live_display and display_q is not None:
                display_q.put({"type": "status", "data": "Complete!"})
                time.sleep(1)  
                display_q.put({"type": "shutdown"})
                if display_proc:
                    display_proc.join(timeout=2)

    return procs