import yfinance as yf
from datetime import datetime, timedelta

def analyze_options(tickers=None, target_date=None, num_expirations=5, num_strikes=5):
    print("=== Starting analyze_options ===")
    
    # Simple test with just one well-known ticker
    if tickers is None:
        tickers = ["QQQ"]
    
    ticker = tickers[0] if tickers else "QQQ"
    print(f"Testing with ticker: {ticker}")
    
    try:
        # Test basic yfinance functionality
        print("Creating yfinance ticker object...")
        stock = yf.Ticker(ticker)
        
        print("Getting options expiration dates...")
        expiry_dates = list(stock.options)
        print(f"Found {len(expiry_dates)} expiration dates")
        
        if not expiry_dates:
            print("No expiration dates found!")
            return create_empty_script()
            
        print(f"First few expiration dates: {expiry_dates[:3]}")
        
        # Use first expiration date for testing
        expiry = expiry_dates[0]
        print(f"Using expiration date: {expiry}")
        
        print("Getting option chain...")
        chain = stock.option_chain(expiry)
        calls = chain.calls
        puts = chain.puts
        
        print(f"Got calls: {len(calls)} rows, puts: {len(puts)} rows")
        
        if calls.empty and puts.empty:
            print("Both calls and puts are empty!")
            return create_empty_script()
            
        # Get some basic data
        if not calls.empty:
            calls_with_oi = calls[calls['openInterest'] > 0]
            top_calls = calls_with_oi.nlargest(3, 'openInterest')
            call_strikes = top_calls['strike'].tolist() if not top_calls.empty else []
            print(f"Top call strikes: {call_strikes}")
        else:
            call_strikes = []
            print("No calls data")
            
        if not puts.empty:
            puts_with_oi = puts[puts['openInterest'] > 0]
            top_puts = puts_with_oi.nlargest(3, 'openInterest')
            put_strikes = top_puts['strike'].tolist() if not top_puts.empty else []
            print(f"Top put strikes: {put_strikes}")
        else:
            put_strikes = []
            print("No puts data")
            
        # Generate minimal working script
        thinkscript = """
# JJAI Levels - Minimal Test
# Developed by Juan Pablo Fajardo

def aggregationPeriod = AggregationPeriod.DAY;
def LastPrice = close(priceType = PriceType.LAST);

# Support levels (calls)
"""
        
        # Add call strikes
        for i, strike in enumerate(call_strikes[:3]):
            thinkscript += f"plot Support{i+1} = {strike:.2f};\n"
            thinkscript += f"Support{i+1}.SetDefaultColor(CreateColor(0, 236, 59));\n"
            
        thinkscript += "\n# Resistance levels (puts)\n"
        
        # Add put strikes
        for i, strike in enumerate(put_strikes[:3]):
            thinkscript += f"plot Resistance{i+1} = {strike:.2f};\n"
            thinkscript += f"Resistance{i+1}.SetDefaultColor(CreateColor(255, 17, 17));\n"
            
        print(f"Generated script length: {len(thinkscript)} characters")
        print("=== analyze_options completed successfully ===")
        
        return {
            'thinkscript': thinkscript,
            'full_output': 'Debug output',
            'execution_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"ERROR in analyze_options: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return create_empty_script()

def create_empty_script():
    return {
        'thinkscript': """# JJAI Levels - Error State
# No data could be retrieved

def aggregationPeriod = AggregationPeriod.DAY;
def LastPrice = close(priceType = PriceType.LAST);

plot NoData = Double.NaN;
""",
        'full_output': 'Error occurred',
        'execution_time': datetime.now().isoformat()
    }

# Test function
if __name__ == "__main__":
    print("Running standalone test...")
    result = analyze_options(["QQQ"], "2025-12-31", 1, 3)
    print(f"Script length: {len(result['thinkscript'])}")
    print("Script content:")
    print(result['thinkscript'])
