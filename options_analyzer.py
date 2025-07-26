import yfinance as yf
from datetime import datetime, timedelta
import io
from contextlib import redirect_stdout

def analyze_options(tickers=None, target_date=None, num_expirations=5, num_strikes=5):
    if tickers is None:
        tickers = ["QQQ", "SPY", "DIA", "IWM", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "NFLX",
                   "TSLA", "AMD", "META", "NET", "ALAB", "EL", "SYM", "ZETA", "SOXL"]
    if target_date is None:
        target_date = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')


    # Capture all print output
    captured_output = io.StringIO()

    with redirect_stdout(captured_output):
        current_datetime = datetime.now()
        print(f"# Script executed on: {current_datetime}\n")

        data = {}

        for ticker in tickers:
            stock = yf.Ticker(ticker)
            try:
                expiry_dates = list(stock.options)
            except Exception as e:
                print(f"# ERROR: Could not retrieve options for {ticker}: {e}")
                continue

            if not expiry_dates:
                print(f"# WARNING: No expirations found for {ticker}")
                continue

            # Sort by closeness to the target date
            expiry_dates.sort(
                key=lambda x: abs(
                    (datetime.strptime(x, '%Y-%m-%d') - datetime.strptime(target_date, '%Y-%m-%d')).days
                )
            )

            data[ticker] = {
                "expiry_dates": [],
                "calls_strike_values_oi": [],
                "puts_strike_values_oi": []
            }

            for i in range(min(num_expirations, len(expiry_dates))):
                expiry = expiry_dates[i]

                try:
                    chain = stock.option_chain(expiry)
                    calls, puts = chain.calls, chain.puts
                except Exception as e:
                    print(f"# ERROR fetching options chain for {ticker} at {expiry}: {e}")
                    continue

                if calls.empty or puts.empty:
                    continue

                top_calls = calls.sort_values('openInterest', ascending=False).head(num_strikes)
                top_puts = puts.sort_values('openInterest', ascending=False).head(num_strikes)

                data[ticker]["expiry_dates"].append(expiry)
                data[ticker]["calls_strike_values_oi"].append(top_calls.strike.values)
                data[ticker]["puts_strike_values_oi"].append(top_puts.strike.values)

        # Print expiration dates used
        for ticker in data:
            dates = data[ticker]["expiry_dates"]
            if dates:
                print(f"# Expiry Dates Used for {ticker}: {', '.join(dates)}\n")

        # Generate ThinkScript
        thinkscript = """
# JJAI Levels
# Developed by Juan Pablo Fajardo

def aggregationPeriod = AggregationPeriod.DAY;
def LastPrice = close(priceType = PriceType.LAST);\n"""

        for ticker in data:
            for i, exp_date in enumerate(data[ticker]["expiry_dates"]):
                thinkscript += f"\n# Expiration Date: {exp_date} - {ticker}"

                for j in range(len(data[ticker]["calls_strike_values_oi"][i])):
                    thinkscript += f"\nplot oi_call_{ticker}_{i + 1}_{j + 1};"
                for j in range(len(data[ticker]["puts_strike_values_oi"][i])):
                    thinkscript += f"\nplot oi_put_{ticker}_{i + 1}_{j + 1};"

                thinkscript += f"\nif (GetSymbol() == \"{ticker}\") {{"
                for j, val in enumerate(data[ticker]["calls_strike_values_oi"][i]):
                    thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1} = {val:.2f};"
                for j, val in enumerate(data[ticker]["puts_strike_values_oi"][i]):
                    thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1} = {val:.2f};"
                thinkscript += "} else {"
                for j in range(len(data[ticker]["calls_strike_values_oi"][i])):
                    thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1} = Double.NaN;"
                for j in range(len(data[ticker]["puts_strike_values_oi"][i])):
                    thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1} = Double.NaN;"
                thinkscript += "};"

                for j in range(len(data[ticker]["calls_strike_values_oi"][i])):
                    thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1}.SetDefaultColor(CreateColor(0, 236, 59));"
                for j in range(len(data[ticker]["puts_strike_values_oi"][i])):
                    thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1}.SetDefaultColor(CreateColor(255, 17, 17));"

                for j in range(len(data[ticker]["calls_strike_values_oi"][i])):
                    thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1}.SetLineWeight({min(5, max(1, 6 - j))});"
                for j in range(len(data[ticker]["puts_strike_values_oi"][i])):
                    thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1}.SetLineWeight({min(5, max(1, 6 - j))});"

        print(thinkscript)

    return {
        'thinkscript': thinkscript,
        'full_output': captured_output.getvalue(),
        'execution_time': datetime.now().isoformat()
    }

# Optional local test
if __name__ == "__main__":
    test_tickers = ["QQQ", "SPY"]
    result = analyze_options(test_tickers, "2025-07-25", 3, 3)
    print(result['thinkscript'])
