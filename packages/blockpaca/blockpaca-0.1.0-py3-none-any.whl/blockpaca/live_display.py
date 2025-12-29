"""
Live Trading Display Module
Uses Rich library to create a non-scrolling, live-updating terminal display
for portfolio state and trade updates.
"""

import time
from collections import deque
from multiprocessing import Process, Queue
from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box


class TradingDisplay:
    """
    A live terminal display for trading systems.
    Shows portfolio state and recent trade updates without scrolling.
    """
    
    def __init__(self, max_trade_updates: int = 15):
        self.console = Console()
        self.max_trade_updates = max_trade_updates
        self.trade_updates = deque(maxlen=max_trade_updates)
        self.portfolio_data = None
        self.realized_pnl = 0.0
        self.available_capital = 100_000.0
        self.status_message = "Initializing..."
        
    def _create_portfolio_table(self) -> Table:
        """Create the portfolio positions table."""
        table = Table(
            title="[bold cyan]Portfolio Positions[/bold cyan]",
            box=box.ROUNDED,
            header_style="bold white on dark_blue",
            border_style="cyan",
            title_style="bold cyan",
            expand=True,
        )
        
        table.add_column("Asset", style="bold white", justify="left", min_width=8)
        table.add_column("Qty", justify="right", min_width=6)
        table.add_column("Cost Basis", justify="right", min_width=12)
        table.add_column("Last Px", justify="right", min_width=10)
        table.add_column("Mkt Value", justify="right", min_width=12)
        table.add_column("Unrealized P&L", justify="right", min_width=14)
        table.add_column("% Change", justify="right", min_width=10)
        
        if self.portfolio_data and len(self.portfolio_data) > 0:
            for row in self.portfolio_data:
                asset = row.get("Asset", "")
                qty = row.get("Qty", 0)
                cost_basis = row.get("Cost Basis", 0)
                last_px = row.get("Last Px")
                market_value = row.get("Market Value", 0)
                unrealized_pnl = row.get("Unrealized P&L", 0)
                pct_change = row.get("% Change (All Time)", 0)
                
                # Style based on P&L
                if asset == "TOTAL":
                    style = "bold yellow"
                    pnl_style = "bold green" if unrealized_pnl >= 0 else "bold red"
                else:
                    style = "white"
                    pnl_style = "green" if unrealized_pnl >= 0 else "red"
                
                # Format values
                qty_str = f"{qty:.1f}" if qty is not None else "-"
                cb_str = f"${cost_basis:,.2f}" if cost_basis is not None else "-"
                px_str = f"${last_px:,.2f}" if last_px is not None else "-"
                mv_str = f"${market_value:,.2f}" if market_value is not None else "-"
                pnl_str = f"${unrealized_pnl:+,.2f}" if unrealized_pnl is not None else "-"
                pct_str = f"{pct_change:+.3f}%" if pct_change is not None else "-"
                
                table.add_row(
                    Text(str(asset), style=style),
                    Text(qty_str, style=style),
                    Text(cb_str, style=style),
                    Text(px_str, style=style),
                    Text(mv_str, style=style),
                    Text(pnl_str, style=pnl_style),
                    Text(pct_str, style=pnl_style),
                )
        else:
            table.add_row(
                Text("No positions", style="dim italic"),
                "-", "-", "-", "-", "-", "-"
            )
        
        return table
    
    def _create_trade_updates_panel(self) -> Panel:
        """Create the trade updates panel."""
        lines = []
        
        if not self.trade_updates:
            lines.append(Text("Waiting for trades...", style="dim italic"))
        else:
            for update in self.trade_updates:
                timestamp = update.get("timestamp", 0)
                time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                ticker = update.get("ticker", "???")
                status = update.get("status", "unknown")
                side = update.get("side", "")
                qty = update.get("executed_qty", 0)
                price = update.get("executed_price", 0)
                
                # Color based on status
                if status == "filled":
                    status_style = "bold green"
                    symbol = "✓"
                elif status == "pending_new" or status == "new":
                    status_style = "yellow"
                    symbol = "◌"
                elif status == "rejected" or status == "error":
                    status_style = "bold red"
                    symbol = "✗"
                else:
                    status_style = "white"
                    symbol = "•"
                
                # Side styling
                side_style = "cyan" if side == "buy" else "magenta"
                
                if status == "filled" and price > 0:
                    line = Text()
                    line.append(f"{time_str} ", style="dim")
                    line.append(f"{symbol} ", style=status_style)
                    line.append(f"{side.upper():4} ", style=side_style)
                    line.append(f"{ticker:6} ", style="bold white")
                    line.append(f"x{qty:.0f} ", style="white")
                    line.append(f"@ ${price:.2f} ", style="white")
                    line.append(f"[{status}]", style=status_style)
                else:
                    line = Text()
                    line.append(f"{time_str} ", style="dim")
                    line.append(f"{symbol} ", style=status_style)
                    line.append(f"{side.upper():4} " if side else "     ", style=side_style)
                    line.append(f"{ticker:6} ", style="bold white")
                    line.append(f"[{status}]", style=status_style)
                
                lines.append(line)
        
        content = Group(*lines) if lines else Text("No updates", style="dim")
        
        return Panel(
            content,
            title="[bold magenta]Trade Updates[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    
    def _create_status_bar(self) -> Panel:
        """Create the status bar with account summary."""
        realized_style = "green" if self.realized_pnl >= 0 else "red"
        
        status_text = Text()
        status_text.append("💰 Available: ", style="dim")
        status_text.append(f"${self.available_capital:,.2f}", style="bold white")
        status_text.append("  │  ", style="dim")
        status_text.append("📈 Realized P&L: ", style="dim")
        status_text.append(f"${self.realized_pnl:+,.2f}", style=f"bold {realized_style}")
        status_text.append("  │  ", style="dim")
        status_text.append("⏱ ", style="dim")
        status_text.append(self.status_message, style="italic cyan")
        
        return Panel(
            status_text,
            box=box.SIMPLE,
            style="on grey11",
            padding=(0, 1),
        )
    
    def _create_header(self) -> Panel:
        """Create the header panel."""
        header_text = Text()
        header_text.append("⚡ ", style="yellow")
        header_text.append("LIVE TRADING DASHBOARD", style="bold white")
        header_text.append(" ⚡", style="yellow")
        
        return Panel(
            header_text,
            box=box.DOUBLE,
            style="bold cyan on grey15",
            padding=(0, 2),
        )
    
    def generate_display(self) -> Layout:
        """Generate the complete display layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="status", size=3),
            Layout(name="main"),
            Layout(name="updates", size=min(self.max_trade_updates + 4, 20)),
        )
        
        layout["header"].update(self._create_header())
        layout["status"].update(self._create_status_bar())
        layout["main"].update(self._create_portfolio_table())
        layout["updates"].update(self._create_trade_updates_panel())
        
        return layout
    
    def update_portfolio(self, portfolio_data: list, realized_pnl: float = 0.0, available_capital: float = 100_000.0):
        """Update portfolio data."""
        self.portfolio_data = portfolio_data
        self.realized_pnl = realized_pnl
        self.available_capital = available_capital
    
    def add_trade_update(self, update: dict):
        """Add a trade update to the display."""
        self.trade_updates.appendleft(update)
    
    def set_status(self, message: str):
        """Set the status message."""
        self.status_message = message


def live_display_worker(
    display_queue: Queue,
    refresh_rate: float = 0.5,
    max_trade_updates: int = 15
):
    """
    Worker process that runs the live display.
    
    Receives updates via display_queue with format:
    {
        "type": "portfolio" | "trade" | "status" | "shutdown",
        "data": <payload>
    }
    """
    display = TradingDisplay(max_trade_updates=max_trade_updates)
    
    with Live(display.generate_display(), refresh_per_second=1/refresh_rate, screen=True) as live:
        running = True
        while running:
            # Process all available messages
            while True:
                try:
                    msg = display_queue.get_nowait()
                    msg_type = msg.get("type")
                    
                    if msg_type == "shutdown":
                        running = False
                        break
                    elif msg_type == "portfolio":
                        display.update_portfolio(
                            msg.get("data", []),
                            msg.get("realized_pnl", 0.0),
                            msg.get("available_capital", 100_000.0)
                        )
                    elif msg_type == "trade":
                        display.add_trade_update(msg.get("data", {}))
                    elif msg_type == "status":
                        display.set_status(msg.get("data", ""))
                        
                except Exception:
                    break
            
            if running:
                live.update(display.generate_display())
                time.sleep(refresh_rate)


def start_live_display(
    refresh_rate: float = 0.5,
    max_trade_updates: int = 15
) -> tuple[Process, Queue]:
    """
    Start the live display in a separate process.
    
    Returns:
        tuple: (Process, Queue) - The display process and the queue to send updates
    
    Usage:
        display_proc, display_q = start_live_display()
        
        # Send portfolio updates
        display_q.put({
            "type": "portfolio",
            "data": [...],  # List of position dicts
            "realized_pnl": 100.0,
            "available_capital": 99000.0
        })
        
        # Send trade updates
        display_q.put({
            "type": "trade",
            "data": {"ticker": "AAPL", "status": "filled", ...}
        })
        
        # Send status updates
        display_q.put({"type": "status", "data": "Running strategy..."})
        
        # Shutdown
        display_q.put({"type": "shutdown"})
        display_proc.join()
    """
    display_queue = Queue()
    display_proc = Process(
        target=live_display_worker,
        args=(display_queue, refresh_rate, max_trade_updates),
        daemon=True
    )
    display_proc.start()
    return display_proc, display_queue


# Test the display
if __name__ == "__main__":
    import random
    
    display_proc, display_q = start_live_display()
    
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN"]
    
    # Simulate some activity
    try:
        for i in range(30):
            # Random portfolio data
            portfolio = []
            total_cost = 0
            total_value = 0
            total_pnl = 0
            
            for ticker in random.sample(tickers, random.randint(3, 6)):
                qty = random.randint(1, 50)
                cost_basis = random.uniform(100, 500) * qty
                pnl = random.uniform(-50, 50)
                market_value = cost_basis + pnl
                
                portfolio.append({
                    "Asset": ticker,
                    "Qty": qty,
                    "Cost Basis": cost_basis,
                    "Last Px": market_value / qty if qty > 0 else 0,
                    "Market Value": market_value,
                    "Unrealized P&L": pnl,
                    "% Change (All Time)": (pnl / cost_basis * 100) if cost_basis > 0 else 0,
                })
                total_cost += cost_basis
                total_value += market_value
                total_pnl += pnl
            
            # Add total row
            portfolio.append({
                "Asset": "TOTAL",
                "Qty": sum(p["Qty"] for p in portfolio),
                "Cost Basis": total_cost,
                "Last Px": None,
                "Market Value": total_value,
                "Unrealized P&L": total_pnl,
                "% Change (All Time)": (total_pnl / total_cost * 100) if total_cost > 0 else 0,
            })
            
            display_q.put({
                "type": "portfolio",
                "data": portfolio,
                "realized_pnl": random.uniform(-100, 200),
                "available_capital": 100000 - total_cost,
            })
            
            # Random trade updates
            if random.random() > 0.5:
                display_q.put({
                    "type": "trade",
                    "data": {
                        "timestamp": time.time(),
                        "ticker": random.choice(tickers),
                        "status": random.choice(["pending_new", "new", "filled", "filled"]),
                        "side": random.choice(["buy", "sell"]),
                        "executed_qty": random.randint(1, 20),
                        "executed_price": random.uniform(100, 500),
                    }
                })
            
            display_q.put({"type": "status", "data": f"Iteration {i+1}/30 - Running..."})
            time.sleep(1)
        
        display_q.put({"type": "status", "data": "Complete!"})
        time.sleep(2)
        
    finally:
        display_q.put({"type": "shutdown"})
        display_proc.join(timeout=2)