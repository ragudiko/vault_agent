"""
html_report_generator.py
Step 3: Generate Firefox-compatible HTML reports
"""

from datetime import datetime
import re


class HTMLReportGenerator:
    """Generates Firefox-compatible HTML test reports."""
    
    @staticmethod
    def parse_pytest_output(output):
        """Parse pytest output to extract statistics."""
        total = passed = failed = 0
        
        if output:
            passed_match = re.search(r'(\d+) passed', output)
            failed_match = re.search(r'(\d+) failed', output)
            
            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))
            
            total = passed + failed
        
        return total, passed, failed
    
    @staticmethod
    def generate(feature, results, doc_url):
        """Generate HTML report."""
        total, passed, failed = HTMLReportGenerator.parse_pytest_output(
            results.get('output', '')
        )
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vault {feature.upper()} Test Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .card h3 {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
        .card .value {{ font-size: 2.5em; font-weight: bold; }}
        .total .value {{ color: #667eea; }}
        .passed .value {{ color: #28a745; }}
        .failed .value {{ color: #dc3545; }}
        .rate .value {{ color: #17a2b8; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 15px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .output {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .output pre {{ margin: 0; white-space: pre-wrap; }}
        .citation {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
        }}
        .citation a {{ color: #0056b3; text-decoration: none; }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Vault {feature.upper()} Test Report</h1>
            <p>Automated Test Results</p>
        </div>
        
        <div class="summary">
            <div class="card total">
                <h3>Total Tests</h3>
                <div class="value">{total}</div>
            </div>
            <div class="card passed">
                <h3>Passed</h3>
                <div class="value">{passed}</div>
            </div>
            <div class="card failed">
                <h3>Failed</h3>
                <div class="value">{failed}</div>
            </div>
            <div class="card rate">
                <h3>Pass Rate</h3>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 Test Results</h2>
                <div class="output">
                    <pre>{results.get('output', 'No output')}</pre>
                </div>
            </div>
            
            <div class="section">
                <h2>📚 Documentation</h2>
                <div class="citation">
                    <strong>Feature:</strong> {feature.upper()}<br>
                    <strong>URL:</strong> <a href="{doc_url}" target="_blank">{doc_url}</a><br>
                    <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by IBM watsonx.ai Vault Test Agent</p>
        </div>
    </div>
</body>
</html>"""
        
        return html


if __name__ == "__main__":
    test_results = {
        'success': True,
        'output': '8 passed in 2.34s'
    }
    
    html = HTMLReportGenerator.generate('kv2', test_results, 'https://example.com')
    
    with open('vault_agent_test_report.html', 'w') as f:
        f.write(html)
    
    print("Report generated: vault_agent_test_report.html")
