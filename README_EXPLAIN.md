# AI Security Agent

This project contains an autonomous AI agent capable of analyzing code for vulnerabilities, researching fixes, applying them, and verifying the results with tests.

## Project Structure

- `agent.py`: The main autonomous agent script (Asynchronous).
- `file_reader.py`: The target file containing a vulnerability.
- `test_file_reader.py`: Test suite to verify functionality and security.
- `REPORT.md`: Generated report detailing the analysis and fix process.
- `REPORT_TEMPLATE.md`: Template used for the report.
- `requirements.txt`: Project dependencies.
- `.env`: Configuration file for API keys.

## How `agent.py` Works

The agent uses an asynchronous, event-driven architecture to efficiently analyze and fix code.

### 1. Initialization & Async Setup
- Loads environment variables (`OPENAI_API_KEY`).
- Initializes the `AsyncOpenAI` client.
- Sets up the `asyncio` event loop to manage concurrent tasks.

### 2. Code Analysis (LLM)
- Reads the target file (defaults to `file_reader.py`, but can be specified via command line).
- Sends the code to GPT-4o to identify security vulnerabilities (e.g., CWE-22, CWE-601, CWE-94, CWE-78).
- The LLM returns a JSON object containing:
    - Vulnerability Type
    - Description
    - List of authoritative research URLs (CWE, OWASP).

### 3. Parallel Research Prefetching
- The agent extracts research URLs from the analysis.
- Uses `aiohttp` to fetch content from **all** research URLs **concurrently**.
- This "prefetching" strategy significantly reduces wait times compared to sequential requests.
- Content is parsed and cleaned (using `BeautifulSoup`) to remove HTML clutter before being used as context.

### 4. Intelligent Fix Generation
- The agent prompts the LLM with:
    - Original Vulnerable Code
    - Vulnerability Analysis
    - Prefetched Research Content (Context)
- The LLM generates a secure, robust fix using standard library modules where possible.
- **Strict Constraints**: The agent enforces that no markdown formatting is included in the returned code, ensuring immediate executability.

### 5. Application & Backup
- Creates a backup of the original code (`<filename>.py.bak`).
- Overwrites the target file with the newly generated secure code.

### 6. Asynchronous Testing
- Runs the `pytest` suite using `asyncio.create_subprocess_exec`.
- Captures standard output and error streams to verify if the fix passed all security and functionality tests.

### 7. Comprehensive Reporting
- Generates `REPORT.md` using a dedicated prompt.
- **Dynamic Context**: Injects the current timestamp (`datetime.now()`) and detailed execution metrics (API call count, test duration).
- **Smart Formatting**: The agent is instructed to avoid placeholders (like `[CVE-...]`) and populate real data or explicit "N/A" markers.
- The report includes:
    - Vulnerability Summary & Analysis
    - Research Findings
    - Fix Strategy & Code Changes
    - Test Results (Pass/Fail status and output)

## How to Run

1.  **Setup Environment**:
    Ensure your `.env` file contains your `OPENAI_API_KEY`.
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run on Default Target**:
    ```bash
    python agent.py
    ```
    This analyzes and fixes `file_reader.py`.

3.  **Run on Specific File**:
    ```bash
    python agent.py path/to/vulnerable_file.py
    ```
