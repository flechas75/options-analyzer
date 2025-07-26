import yfinance as yf
from datetime import datetime, timedelta
import io
from contextlib import redirect_stdout
import pandas as pd

def analyze_options(tickers=None, target_date=None, num_expirations=5, num_strikes=5):
    print(f"=== analyze_options called ===")
    print(f"Parameters: tickers={tickers}, target_date={target_date}, num_expirations={num_expirations}, num_strikes={num_strikes}")
    
    if tickers is None:
        tickers = ["QQQ", "SPY", "DIA", "IWM", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "NFLX",
                   "TSLA", "AMD", "META", "NET", "ALAB", "EL", "SYM", "ZETA", "SOXL"]
    print(f"Using tickers: {tickers}")
    
    if target_date is None:
        target_date = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
    print(f"Using target_date: {target_date}")

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
                stock = yf.Ticker(ticker)
                print(f"Created yfinance Ticker object for {ticker}")
                
                # Get available expiration dates
                try:
                    expiry_dates = list(stock.options)
                    print(f"Found {len(expiry_dates)} expiration dates for {ticker}")
                    if not expiry_dates:
                        print(f"No expiration dates found for {ticker}")
                        continue
                except Exception as e:
                    print(f"ERROR getting options for {ticker}: {e}")
                    continue

                # Sort by closeness to target date
                try:
                    expiry_dates.sort(
                        key=lambda x: abs(
                            (datetime.strptime(x, '%Y-%m-%d') - datetime.strptime(target_date, '%Y-%m-%d')).days
                        )
                    )
                    print(f"Sorted expiration dates: {expiry_dates[:5]}")
                except Exception as e:
                    print(f"ERROR sorting expiration dates: {e}")
                    continue

                data[ticker] = {
                    "expiry_dates": [],
                    "calls_strike_values_oi": [],
                    "puts_strike_values_oi": []
                }

                process_count = min(num_expirations, len(expiry_dates))
                print(f"Will process {process_count} expiration dates")

                # Process each expiration date
                for i in range(process_count):
                    expiry = expiry_dates[i]
                    print(f"  Processing expiration {i+1}/{process_count}: {expiry}")
                    
                    try:
                        # Get calls and puts separately (like in your working Dash code)
                        print(f"    Fetching calls for {ticker} at {expiry}")
                        calls = stock.option_chain(expiry).calls
                        print(f"    Got {len(calls)} calls")
                        
                        print(f"    Fetching puts for {ticker} at {expiry}")
                        puts = stock.option_chain(expiry).puts
                        print(f"    Got {len(puts)} puts")
                        
                    except Exception as e:
                        print(f"    ERROR fetching option chain for {ticker} at {expiry}: {e}")
                        continue

                    # Get top strikes by open interest (like in your working code)
                    try:
                        if not calls.empty:
                            top_calls = calls.nlargest(num_strikes, 'openInterest')
                            top_calls = top_calls[top_calls['openInterest'] > 0]  # Only positive OI
                            call_strikes = top_calls['strike'].values if not top_calls.empty else []
                            print(f"    Top {len(call_strikes)} call strikes by OI: {call_strikes}")
                        else:
                            call_strikes = []
                            print(f"    No calls data")
                            
                        if not puts.empty:
                            top_puts = puts.nlargest(num_strikes, 'openInterest')
                            top_puts = top_puts[top_puts['openInterest'] > 0]  # Only positive OI
                            put_strikes = top_puts['strike'].values if not top_puts.empty else []
                            print(f"    Top {len(put_strikes)} put strikes by OI: {put_strikes}")
                        else:
                            put_strikes = []
                            print(f"    No puts data")
                            
                    except Exception as e:
                        print(f"    ERROR processing top strikes: {e}")
                        call_strikes = []
                        put_strikes = []
                        continue

                    # Only add if we have data
                    if len(call_strikes) > 0 or len(put_strikes) > 0:
                        data[ticker]["expiry_dates"].append(expiry)
                        data[ticker]["calls_strike_values_oi"].append(call_strikes)
                        data[ticker]["puts_strike_values_oi"].append(put_strikes)
                        print(f"    Added {len(call_strikes)} calls and {len(put_strikes)} puts for {ticker}")
                    else:
                        print(f"    No strikes with positive OI found for {ticker} at {expiry}")

                print(f"  Finished processing {ticker}. Collected data for {len(data[ticker]['expiry_dates'])} expirations")
                
            except Exception as e:
                print(f"FATAL ERROR processing {ticker}: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                continue

        print(f"=== Finished processing all tickers ===")
        print(f"Data collected for {len(data)} tickers: {list(data.keys())}")

        # Print expiration dates used
        for ticker in 
            dates = data[ticker]["expiry_dates"]
            if dates:
                print(f"# Expiry Dates Used for {ticker}: {', '.join(dates)}")

        # Generate ThinkScript
        print("Generating ThinkScript...")
        thinkscript = """
# JJAI Levels
# Developed by Juan Pablo Fajardo

def aggregationPeriod = AggregationPeriod.DAY;
def LastPrice = close(priceType = PriceType.LAST);\n"""

        total_plots = 0
        for ticker in 
            for i, exp_date in enumerate(data[ticker]["expiry_dates"]):
                thinkscript += f"\n# Expiration Date: {exp_date} - {ticker}"

                call_count = len(data[ticker]["calls_strike_values_oi"][i])
                put_count = len(data[ticker]["puts_strike_values_oi"][i])
                total_plots += call_count + put_count
                
                print(f"  Generating for {ticker} expiration {exp_date}: {call_count} calls, {put_count} puts")

                # Generate plot declarations
                for j in range(call_count):
                    thinkscript += f"\nplot oi_call_{ticker}_{i + 1}_{j + 1};"
                for j in range(put_count):
                    thinkscript += f"\nplot oi_put_{ticker}_{i + 1}_{j + 1};"

                # Generate value assignments
                thinkscript += f"\nif (GetSymbol() == \"{ticker}\") {{"
                
                for j, val in enumerate(data[ticker]["calls_strike_values_oi"][i]):
                    thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1} = {val:.2f};"
                for j, val in enumerate(data[ticker]["puts_strike_values_oi"][i]):
                    thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1} = {val:.2f};"
                    
                thinkscript += "} else {"
                
                for j in range(call_count):
                    thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1} = Double.NaN;"
                for j in range(put_count):
                    thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1} = Double.NaN;"
                    
                thinkscript += "};"

                # Generate styling
                for j in range(call_count):
                    thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1}.SetDefaultColor(CreateColor(0, 236, 59));"
                for j in range(put_count):
                    thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1}.SetDefaultColor(CreateColor(255, 17, 17));"

                for j in range(call_count):
                    thinkscript += f"\noi_call_{ticker}_{i + 1}_{j + 1}.SetLineWeight({min(5, max(1, 6 - j))});"
                for j in range(put_count):
                    thinkscript += f"\noi_put_{ticker}_{i + 1}_{j + 1}.SetLineWeight({min(5, max(1, 6 - j))});"

        print(f"ThinkScript generated with {total_plots} total plots")
        print(f"Final ThinkScript length: {len(thinkscript)} characters")
        
        if total_plots == 0:
            thinkscript = """
# JJAI Levels
# Developed by Juan Pablo Fajardo
# No options data found for the specified parameters

def aggregationPeriod = AggregationPeriod.DAY;
def LastPrice = close(priceType = PriceType.LAST);

# No significant options open interest found
plot NoData = Double.NaN;
"""
            print("WARNING: No options data found - generating empty script")

    result = {
        'thinkscript': thinkscript,
        'full_output': captured_output.getvalue(),
        'execution_time': datetime.now().isoformat()
    }
    print(f"=== analyze_options completed ===")
    return result

# Test function
if __name__ == "__main__":
    print("Running test...")
    result = analyze_options(["NVDA"], "2025-08-01", 1, 1)
    print(f"Test completed. Script length: {len(result['thinkscript'])}")
    if len(result['thinkscript']) < 500:
        print("Script content:")
        print(result['thinkscript'])
