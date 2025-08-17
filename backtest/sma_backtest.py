# Simple SMA crossover backtest to produce CSV, chart, and metrics.
import pandas as pd, yfinance as yf, matplotlib.pyplot as plt, sys, pathlib, json
from datetime import datetime, timedelta

out_dir = pathlib.Path(__file__).parent / "results"
out_dir.mkdir(parents=True, exist_ok=True)

ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
start = (datetime.today() - timedelta(days=365*2)).strftime("%Y-%m-%d")
df = yf.download(ticker, start=start, auto_adjust=True)
df = df.rename_axis("date").reset_index()
df["SMA50"] = df["Close"].rolling(50).mean()
df["SMA200"] = df["Close"].rolling(200).mean()
df.dropna(inplace=True)

df["signal"] = 0
df.loc[df["SMA50"] > df["SMA200"], "signal"] = 1
df["position"] = df["signal"].diff().fillna(0)

# Compute daily returns
df["ret"] = df["Close"].pct_change().fillna(0.0)
df["strategy"] = df["ret"] * df["signal"].shift(1).fillna(0.0)
equity = (1 + df["strategy"]).cumprod()

# Save CSV
csv_path = out_dir / f"{ticker}_signals.csv"
df.to_csv(csv_path, index=False)

# Metrics
cagr = equity.iloc[-1] ** (252/len(equity)) - 1
vol = df["strategy"].std() * (252 ** 0.5)
sharpe = (df["strategy"].mean() / df["strategy"].std()) * (252 ** 0.5) if df["strategy"].std() else 0.0
metrics = {"ticker": ticker, "cagr": float(cagr), "vol": float(vol), "sharpe": float(sharpe)}
(out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

# Chart
plt.figure()
plt.plot(df["date"], equity, label="Strategy Equity")
plt.title(f"SMA Crossover Strategy — {ticker}")
plt.xlabel("Date")
plt.ylabel("Equity (Start=1.0)")
plt.legend()
png_path = out_dir / f"{ticker}_equity.png"
plt.savefig(png_path, bbox_inches="tight")

print("Wrote:", csv_path, "and", png_path, "metrics:", metrics)
