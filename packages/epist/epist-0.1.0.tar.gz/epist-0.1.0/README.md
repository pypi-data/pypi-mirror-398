# epist

Official Python SDK for the Epist.ai Audio RAG Platform.

## Installation

```bash
pip install epist
```

## Usage

```python
from epist import Epist

client = Epist(api_key="YOUR_API_KEY")

# 1. Upload File
status = client.upload_file("meeting_recording.mp3")
print(f"Task Started: {status['id']}")

# 2. Transcribe URL
task = client.transcribe_url("https://example.com/podcast.mp3")

# 3. Search
results = client.search("quarterly earnings")
for result in results:
    print(f"[{result['score']}] {result['text']}")
```
