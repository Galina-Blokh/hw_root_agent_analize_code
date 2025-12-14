import os
import sys
import asyncio
import time
import json
import re
import datetime
import aiohttp
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API Key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in .env file.")
    print("Please create a .env file with OPENAI_API_KEY=your_key_here")
    sys.exit(1)

client = AsyncOpenAI(api_key=api_key)

TARGET_FILE = "file_reader.py"
TEST_FILE = "test_file_reader.py"
REPORT_FILE = "REPORT.md"
TEMPLATE_FILE = "REPORT_TEMPLATE.md"

# Global counter for API calls
api_call_count = 0

def read_file(path):
    """Read content of a file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None

def write_file(path, content):
    """Write content to a file."""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully wrote to {path}")
        return True
    except Exception as e:
        print(f"Error writing to {path}: {e}")
        return False

async def run_tests():
    """Run pytest asynchronously and return the output and success status."""
    print("Running tests...")
    start_time = time.time()
    try:
        process = await asyncio.create_subprocess_exec(
            "pytest", TEST_FILE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        
        output = stdout.decode() + stderr.decode()
        duration = time.time() - start_time
        return {
            "success": process.returncode == 0,
            "output": output,
            "duration": duration
        }
    except Exception as e:
        return {
            "success": False,
            "output": str(e),
            "duration": time.time() - start_time
        }

async def fetch_url_content(session, url):
    """Fetch and parse content from a URL asynchronously."""
    print(f"Fetching content from: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        async with session.get(url, headers=headers, timeout=10) as response:
            response.raise_for_status()
            text_content = await response.text()
            
            # BS4 parsing
            soup = BeautifulSoup(text_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            text = soup.get_text()
            
            # Clean text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return f"--- Source: {url} ---\n{text[:5000]}\n"
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return f"Error fetching content from {url}: {str(e)}"

async def analyze_code_for_vulnerabilities(code):
    """Analyze code to identify vulnerabilities and suggest research URLs."""
    global api_call_count
    print("Analyzing code for vulnerabilities...")
    
    prompt = f"""
    You are an expert security researcher. Analyze the following Python code for security vulnerabilities.
    
    Code to analyze:
    ```python
    {code}
    ```
    
    Identify the primary security vulnerability (e.g., CWE-22, SQL Injection, etc.).
    Provide your response in JSON format with the following keys:
    - "vulnerability_type": The name/ID of the vulnerability.
    - "description": A brief description of the vulnerability in this code.
    - "research_urls": A list of 2-3 authoritative most relevant and trusted URLs (CWE, OWASP, etc.) to research this specific vulnerability.
    """
    
    api_call_count += 1
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

async def generate_fix(code, analysis, research_content):
    """Generate a fixed version of the code based on analysis and research."""
    global api_call_count
    print("Generating fix...")
    
    prompt = f"""
    You are an expert secure code developer. Fix the vulnerability in the following code.
    
    Vulnerability Analysis:
    {json.dumps(analysis, indent=2)}
    
    Research Content (Reference Material):
    {research_content}
    
    Original Code:
    ```python
    {code}
    ```
    
    Instructions:
    1. Apply a robust fix for the identified vulnerability.
    2. Ensure the code still performs its original intended function.
    3. Use standard library modules where possible.
    4. Return ONLY the complete Python code for the fixed file. NO markdown formatting or explanations outside the code.
    """
    
    api_call_count += 1
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    content = response.choices[0].message.content
    # Clean up code blocks if present
    if "```python" in content:
        content = content.split("```python")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
        
    return content

async def generate_report(template, analysis, research_content, test_results, fix_details):
    """Generate a report based on the template and execution results."""
    global api_call_count
    print("Generating report...")
    
    prompt = f"""
    You are a security analyst. Fill out the following report template based on the provided information.
    
    Current Date: {datetime.datetime.now()}

    Analysis:
    {json.dumps(analysis, indent=2)}
    
    Research Summary:
    {research_content[:1000]}... (truncated)
    
    Test Results:
    Success: {test_results['success']}
    Duration: {test_results['duration']:.2f}s
    Output: {test_results['output'][-500:]} (last 500 chars)
    
    Metrics:
    Total LLM API Calls: {api_call_count + 1} (including this one)
    
    Fix Details:
    The code was patched to validate paths and prevent traversal.
    
    Template:
    {template}
    
    Instructions:
    1. Fill in all the bracketed placeholders [ ] with relevant details.
    2. Keep the markdown structure.
    3. Ensure the content is professional and accurate.
    """
    
    api_call_count += 1
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

async def main():
    start_total_time = time.time()
    
    # 1. Read Code
    if len(sys.argv) > 1:
        target_file_path = sys.argv[1]
    else:
        target_file_path = TARGET_FILE
        
    code_content = read_file(target_file_path)
    if not code_content:
        sys.exit(1)
        
    # 2. Analyze
    analysis = await analyze_code_for_vulnerabilities(code_content)
    print(f"Identified Vulnerability: {analysis['vulnerability_type']}")
    
    # 3. Research (Parallel Fetch)
    research_urls = analysis.get('research_urls', [])
    research_text = ""
    
    if research_urls:
        print(f"Prefetching {len(research_urls)} resources concurrently...")
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_url_content(session, url) for url in research_urls]
            results = await asyncio.gather(*tasks)
            research_text = "\n".join(results)
    
    # 4. Fix
    fixed_code = await generate_fix(code_content, analysis, research_text)
    
    # 5. Apply Fix
    backup_file = target_file_path + ".bak"
    write_file(backup_file, code_content) # Backup original
    write_file(target_file_path, fixed_code)
    
    # 6. Test
    test_results = await run_tests()
    print(f"Tests passed: {test_results['success']}")
    
    # 7. Report
    template = read_file(TEMPLATE_FILE)
    if not template:
        # Fallback template if file not found
        template = "# Security Report\n\n## Vulnerability\n[Desc]\n\n## Fix\n[Fix]\n"
        
    report = await generate_report(template, analysis, research_text, test_results, fixed_code)
    write_file(REPORT_FILE, report)
    
    print(f"Process completed in {time.time() - start_total_time:.2f} seconds.")
    print(f"Report generated at {REPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
