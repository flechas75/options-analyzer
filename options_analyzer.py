import yfinance as yf
from datetime import datetime, timedelta
import io
from contextlib import redirect_stdout

def analyze_options(tickers=None, target_date=None, num_expirations=5, num_strikes=5):
    print(f"=== analyze_options called ===")
    print(f"Parameters received: tickers={tickers}, target_date={target_date}, num_expirations={num_expirations}, num_strikes={num_strikes}")
    
    if tickers is None:
        tickers = ["QQQ", "SPY", "DIA", "IWM", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "NFLX",
                   "TSLA", "AMD", "META", "NET", "ALAB", "EL", "SYM", "ZETA", "SOXL"]
        print(f"No tickers provided, using default: {tickers}")
    else:
        print(f"Using provided tickers: {tickers}")
    
    if target_date is None:
        target_date = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
        print(f"No target_date provided, using default: {target_date}")
    else:
        print(f"Using provided target_date: {target_date}")

    # Capture all print output
    captured_output = io.StringIO()

    with redirect_stdout(captured_output):
        current_datetime = datetime.now()
        print(f"# Script executed on: {current_datetime}\n")

        data = {}
        print(f"Starting to process {len(tickers)} tickers...")

        for ticker_idx, ticker in enumerate(tickers):
            print(f"--- Processing ticker {ticker_idx + 1}/{len(tickers)}: {ticker} ---")
            try:
                print(f"Creating yfinance Ticker object for {ticker}")
                stock = yf.Ticker(ticker)
                
                print(f"Attempting to get options for {ticker}")
                try:
                    expiry_dates = list(stock.options)
                    print(f"Successfully retrieved options for {ticker}: found {len(expiry_dates)} expiration dates")
                except Exception as e:
                    print(f"ERROR: Could not retrieve options for {ticker}: {e}")
                    import traceback
                    print(f"Full traceback: {traceback.format_exc()}")
                    continue

                if not expiry_dates:
                    print(f"WARNING: No expirations found for {ticker}")
                    continue
                else:
                    print(f"Found expiration dates for {ticker}: {expiry_dates[:5]}...")  # Show first 5

                # Sort by closeness to the target date
                print(f"Sorting expiration dates by proximity to target date {target_date}")
                try:
                    expiry_dates.sort(
                        key=lambda x: abs(
                            (datetime.strptime(x, '%Y-%m-%d') - datetime.strptime(target_date, '%Y-%m-%d')).days
                        )
                    )
                    print(f"Sorted expiration dates: {expiry_dates[:5]}...")  # Show first 5
                except Exception as e:
                    print(f"ERROR sorting expiration dates for {ticker}: {e}")
                    continue

                data[ticker] = {
                    "expiry_dates": [],
                    "calls_strike_values_oi": [],
                    "puts_strike_values_oi": []
                }

                process_count = min(num_expirations, len(expiry_dates))
                print(f"Will process {process_count} expiration dates for {ticker}")
                
                for i in range(process_count):
                    expiry = expiry_dates[i]
                    print(f"  Processing expiration {i+1}/{process_count}: {expiry}")

                    try:
                        print(f"    Fetching option chain for {ticker} expiration {expiry}")
                        chain = stock.option_chain(expiry)
                        calls, puts = chain.calls, chain.puts
                        print(f"    Successfully got option chain: {len(calls)} calls, {len(puts)} puts")
                    except Exception as e:
                        print(f"    ERROR fetching options chain for {ticker} at {expiry}: {e}")
                        import traceback
                        print(f"    Full traceback: {traceback.format_exc()}")
                        continue

                    if calls.empty and puts.empty:
                        print(f"    Both calls and puts are empty for {ticker} at {expiry}")
                        continue
                    elif calls.empty:
                        print(f"    Calls are empty for {ticker} at {expiry}")
                    elif puts.empty:
                        print(f"    Puts are empty for {ticker} at {expiry}")

                    print(f"    Sorting by open interest...")
                    try:
                        top_calls = calls.sort_values('openInterest', ascending=False).head(num_strikes) if not calls.empty else calls
                        top_puts = puts.sort_values('openInterest', ascending=False).head(num_strikes) if not puts.empty else puts
                        print(f"    Top calls count: {len(top_calls)}, Top puts count: {len(top_puts)}")
                    except Exception as e:
                        print(f"    ERROR sorting by open interest for {ticker} at {expiry}: {e}")
                        continue

                    if top_calls.empty and top_puts.empty:
                        print(f"    No options with open interest for {ticker} at {expiry}")
                        continue

                    data[ticker]["expiry_dates"].append(expiry)
                    data[ticker]["calls_strike_values_oi"].append(top_calls.strike.values if not top_calls.empty else [])
                    data[ticker]["puts_strike_values_oi"].append(top_puts.strike.values if not top_puts.empty else [])
                    print(f"    Successfully added data for {ticker} expiration {expiry}")

                print(f"  Finished processing {ticker}. Collected data for {len(data[ticker]['expiry_dates'])} expirations")
                
            except Exception as e:
                print(f"FATAL ERROR processing {ticker}: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                continue

        print(f"=== Finished processing all tickers ===")
        print(f"Data collected for {len(data)} tickers: {list(data.keys())}")
        
        # Print expiration dates used
        print("Printing expiration dates used:")
        for ticker in data:
            dates = data[ticker]["expiry_dates"]
            if dates:
                print(f"# Expiry Dates Used for {ticker}: {', '.join(dates)}")
            else:
                print(f"# No expiration dates collected for {ticker}")

        # Generate ThinkScript
        print("Generating ThinkScript...")
        thinkscript = """
# JJAI Levels
# Developed by Juan Pablo Fajardo

def aggregationPeriod = AggregationPeriod.DAY;
def LastPrice = close(priceType = PriceType.LAST);\n"""

        print(f"Generating script for {len(data)} tickers with data")
        ticker_count = 0
        for ticker in data:
            if data[ticker]["expiry_dates"]:  # Only process tickers with data
                ticker_count += 1
                print(f"  Generating script for ticker {ticker_count}: {ticker}")
                for i, exp_date in enumerate(data[ticker]["expiry_dates"]):
                    thinkscript += f"\n# Expiration Date: {exp_date} - {ticker}"

                    call_count = len(data[ticker]["calls_strike_values_oi"][i]) if i < len(data[ticker]["calls_strike_values_oi"]) else 0
                    put_count = len(data[ticker]["puts_strike_values_oi"][i]) if i < len(data[ticker]["puts_strike_values_oi"]) else 0
                    
                    print(f"    Expiration {i+1}: {exp_date}, {call_count} calls, {put_count} puts")

                    for j in range(call_count):
                        thinkscript += f"\nplot oi_call_{ticker}_{i + 1}_{j + 1};"
                    for j in range(put_count):
                        thinkscript += f"\nplot oi_put_{ticker}_{i + 1}_{j + 1};"

                    thinkscript += f"\nif (GetSymbol() == \"{ticker}\") {{"
                    for j, val in enumerate(data[ticker]["calls_strike_values_oi"][i] if i < len(data[ticker]["calls_strike_values_oi"]) else []):
                        thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1} = {val:.2f};"
                    for j, val in enumerate(data[ticker]["puts_strike_values_oi"][i] if i < len(data[ticker]["puts_strike_values_oi"]) else []):
                        thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1} = {val:.2f};"
                    thinkscript += "} else {"
                    for j in range(call_count):
                        thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1} = Double.NaN;"
                    for j in range(put_count):
                        thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1} = Double.NaN;"
                    thinkscript += "};"

                    for j in range(call_count):
                        thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1}.SetDefaultColor(CreateColor(0, 236, 59));"
                    for j in range(put_count):
                        thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1}.SetDefaultColor(CreateColor(255, 17, 17));"

                    for j in range(call_count):
                        thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1}.SetLineWeight({min(5, max(1, 6 - j))});"
                    for j in range(put_count):
                        thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1}.SetLineWeight({min(5, max(1, 6 - j))});"
            else:
                print(f"  Skipping {ticker} - no expiration data collected")

        print(f"ThinkScript generated, final length: {len(thinkscript)} characters")
        if len(thinkscript) < 200:
            print("WARNING: ThinkScript is very short - may indicate no data was processed")
            print("ThinkScript content:")
            print(repr(thinkscript))
        else:
            print(f"Successfully generated ThinkScript with {len(thinkscript)} characters")

    result = {
        'thinkscript': thinkscript,
        'full_output': captured_output.getvalue(),
        'execution_time': datetime.now().isoformat()
    }
    print(f"=== analyze_options completed ===")
    return result

# Optional local test
if __name__ == "__main__":
    print("Running local test...")
    test_tickers = ["QQQ", "SPY"]
    result = analyze_options(test_tickers, "2025-07-25", 3, 3)
    print("Test completed. ThinkScript length:", len(result['thinkscript']))
    print("First 500 chars:", result['thinkscript'][:500])
