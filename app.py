from flask import Flask, render_template_string, request
import json
from options_analyzer import analyze_options

app = Flask(__name__)

# HTML template with ticker input
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Options Analysis Tool - JJAI Levels</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 30px;
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
        }
        .section h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
            align-items: end;
        }
        .control-group {
            flex: 1;
            min-width: 200px;
        }
        .control-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #2c3e50;
        }
        .control-group input, .control-group select, .control-group textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #3498db;
            border-radius: 5px;
            font-size: 16px;
            font-family: inherit;
        }
        .control-group textarea {
            min-height: 120px;
            resize: vertical;
        }
        .btn {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
        }
        .btn:active {
            transform: translateY(-1px);
        }
        .btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .status {
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            text-align: center;
            font-weight: bold;
        }
        .loading {
            background: #fff3cd;
            color: #856404;
        }
        .success {
            background: #d4edda;
            color: #155724;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
        }
        .thinkscript-container {
            background: #1e1e1e;
            color: #d4d4d4;
            border-radius: 8px;
            padding: 25px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #333;
        }
        .thinkscript-container pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
            color: #d4d4d4;
        }
        .ticker-info {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
            border-top: 1px solid #eee;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }
        .config-info {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
            font-size: 0.9em;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 10px;
            }
            .header {
                padding: 20px;
            }
            .header h1 {
                font-size: 2em;
            }
            .content {
                padding: 20px;
            }
            .btn {
                padding: 12px 20px;
                font-size: 16px;
            }
            .controls {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 JJAI Options Analysis Tool</h1>
            <p>Generate Thinkorswim support/resistance levels based on options open interest</p>
        </div>
        <div class="content">
            <div class="section">
                <h2>⚙️ Configuration</h2>
                <form id="configForm">
                    <div class="controls">
                        <div class="control-group">
                            <label for="tickers">Tickers (comma separated)</label>
                            <textarea id="tickers" name="tickers" placeholder="e.g., QQQ,SPY,NVDA,AAPL,MSFT">QQQ,SPY,DIA,IWM,NVDA,AAPL,MSFT,AMZN,GOOGL,NFLX,TSLA,AMD,META,NET,ALAB,EL,SYM,ZETA,SOXL</textarea>
                        </div>
                        <div class="control-group">
                            <label for="targetDate">Target Expiration Date</label>
                            <input type="date" id="targetDate" name="targetDate" value="2025-07-25">
                        </div>
                        <div class="control-group">
                            <label for="numExpirations">Number of Expirations</label>
                            <input type="number" id="numExpirations" name="numExpirations" min="1" max="10" value="5">
                        </div>
                        <div class="control-group">
                            <label for="numStrikes">Strikes per Expiration</label>
                            <input type="number" id="numStrikes" name="numStrikes" min="1" max="10" value="5">
                        </div>
                        <div class="control-group">
                            <button type="button" class="btn" id="runButton" onclick="runAnalysis()">
                                <span id="buttonText">▶ Run Analysis</span>
                            </button>
                        </div>
                    </div>
                </form>
                <div class="config-info">
                    <strong>Tip:</strong> Enter ticker symbols separated by commas. Example: AAPL,MSFT,GOOGL
                </div>
                <div id="status"></div>
            </div>
            <div class="section">
                <h2>ℹ️ Current Configuration</h2>
                <div class="ticker-info">
                    <strong>Tickers:</strong> <span id="currentTickers">QQQ,SPY,DIA,IWM,NVDA,AAPL,MSFT,AMZN,GOOGL,NFLX,TSLA,AMD,META,NET,ALAB,EL,SYM,ZETA,SOXL</span><br>
                    <strong>Target expiration date:</strong> <span id="currentTargetDate">2025-07-25</span><br>
                    <strong>Using:</strong> <span id="currentNumExpirations">6</span> nearest expiration dates, Top <span id="currentNumStrikes">5</span> strikes by open interest
                </div>
            </div>
            <div class="section">
                <h2>💻 Generated ThinkScript</h2>
                <div class="thinkscript-container">
                    <pre id="output">Click "Run Analysis" to generate the ThinkScript...</pre>
                </div>
            </div>
        </div>
        <div class="footer">
            <p>Developed with ❤️ for Options Traders | Thinkorswim Integration</p>
        </div>
    </div>
    <script>
        // Update info display when config changes
        document.getElementById('tickers').addEventListener('input', updateInfo);
        document.getElementById('targetDate').addEventListener('change', updateInfo);
        document.getElementById('numExpirations').addEventListener('change', updateInfo);
        document.getElementById('numStrikes').addEventListener('change', updateInfo);

        function updateInfo() {
            document.getElementById('currentTickers').textContent = document.getElementById('tickers').value || 'None';
            document.getElementById('currentTargetDate').textContent = document.getElementById('targetDate').value;
            document.getElementById('currentNumExpirations').textContent = (parseInt(document.getElementById('numExpirations').value) + 1);
            document.getElementById('currentNumStrikes').textContent = document.getElementById('numStrikes').value;
        }

        async function runAnalysis() {
            const button = document.getElementById('runButton');
            const buttonText = document.getElementById('buttonText');
            const status = document.getElementById('status');
            const output = document.getElementById('output');

            // Get configuration values
            const tickers = document.getElementById('tickers').value;
            const targetDate = document.getElementById('targetDate').value;
            const numExpirations = document.getElementById('numExpirations').value;
            const numStrikes = document.getElementById('numStrikes').value;

            // Validate tickers
            if (!tickers.trim()) {
                status.innerHTML = '<div class="status error">❌ Please enter at least one ticker symbol</div>';
                return;
            }

            // Disable button and show loading
            button.disabled = true;
            buttonText.innerHTML = '<span class="spinner"></span> Analyzing Options...';
            status.innerHTML = '<div class="status loading">Running analysis with your configuration, please wait (this may take 1-2 minutes)...</div>';
            output.textContent = 'Processing...';

            try {
                const response = await fetch(`/api/analyze?tickers=${encodeURIComponent(tickers)}&target_date=${targetDate}&num_expirations=${numExpirations}&num_strikes=${numStrikes}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.status === 'success') {
                    status.innerHTML = '<div class="status success">✅ Analysis completed successfully!</div>';
                   output.innerHTML = '<code>' + data.thinkscript.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</code>';

                } else {
                    throw new Error(data.message || 'Analysis failed');
                }
            } catch (error) {
                status.innerHTML = '<div class="status error">❌ Error: ' + error.message + '</div>';
                output.textContent = 'Failed to generate analysis. Please try again.';
                console.error('Error:', error);
            } finally {
                // Re-enable button
                button.disabled = false;
                buttonText.textContent = '▶ Run Analysis';
            }
        }

        // Initialize with current date + 6 months as default target date
        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date();
            const targetDate = new Date(today.setMonth(today.getMonth() + 6));
            const formattedDate = targetDate.toISOString().split('T')[0];
            document.getElementById('targetDate').value = formattedDate;
            document.getElementById('currentTargetDate').textContent = formattedDate;
        });
    </script>
</body>
</html>
'''

@app.route('/')
@app.route('/api/test')
def test_api():
    """Simple test endpoint to verify the API is working"""
    return {
        'status': 'success',
        'message': 'API is working!',
        'timestamp': 'test'
    }
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analyze')
def api_analyze():
    try:
        # Get parameters from query string
        tickers_str = request.args.get('tickers', '')
        target_date = request.args.get('target_date', '2025-07-25')
        num_expirations = int(request.args.get('num_expirations', 5))
        num_strikes = int(request.args.get('num_strikes', 5))

        # Parse tickers
        if not tickers_str:
            raise ValueError("No tickers provided")

        tickers = [ticker.strip().upper() for ticker in tickers_str.split(',') if ticker.strip()]

        if not tickers:
            raise ValueError("No valid tickers provided")

        # For now, we'll need to modify your analyzer to accept custom tickers
        # This is a placeholder - you'll need to update options_analyzer.py
        results = analyze_options(
            tickers=tickers,
            target_date=target_date,
            num_expirations=num_expirations,
            num_strikes=num_strikes
        )

        return {
            'status': 'success',
            'thinkscript': results['thinkscript'],
            'execution_time': results['execution_time'],
            'parameters': {
                'tickers': tickers,
                'target_date': target_date,
                'num_expirations': num_expirations,
                'num_strikes': num_strikes
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }, 500

application = app

if __name__ == '__main__':
    print("=" * 50)
    print("JJAI Options Analysis Web Server")
    print("=" * 50)
    print("Make sure you have installed the required packages:")
    print("pip install flask yfinance")
    print()
    print("To start the server, run:")
    print("python app.py")
    print()
    print("Then open your browser and go to:")
    print("http://localhost:5000")
    print("OR")
    print("http://127.0.0.1:5000")
    print("=" * 50)
    # Try multiple binding options
    try:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print("Port 5000 is busy, trying port 5001...")
            app.run(host='0.0.0.0', port=5001, debug=True)
        else:
            raise

