# CPUMarkets Python SDK

This package provides a Python SDK and CLI to submit CPU jobs to CPUMarkets.

## Install
```bash
pip install cpumarkets
```

## Configure
```bash
export CPURENT_BASE_URL=https://www.cpu.markets
export CPURENT_API_KEY=YOUR_SDK_KEY
export CPURENT_API_SECRET=YOUR_SDK_SECRET
```

## Python usage
```python
from cpumarkets import CPUMarketsClient

client = CPUMarketsClient(
    base_url="https://www.cpu.markets",
    api_key="YOUR_SDK_KEY",
    api_secret="YOUR_SDK_SECRET",
)

job_id = client.submit_direct_job(
    task_type="hashing",
    payload={"data": "hello", "iterations": 200000},
    requested_cores=1,
    requested_seconds=20,
    priority=0,
)

result = client.wait_for_result(job_id, poll_interval=2, timeout=120)
print(result["output"])
```

## CLI usage
List available listings:
```bash
cpumarkets list
```

Submit a direct job:
```bash
cpumarkets direct --task hashing --payload '{"data":"hello","iterations":200000}' --cores 1 --seconds 20 --wait
```

Run a Python script on rented CPU:
```bash
cpumarkets python3 path/to/script.py --cores 1 --seconds 30 --wait
```

## Notes
- Buyer IP whitelist must allow your server IP.
- Sellers can block countries, which filters visible listings.
