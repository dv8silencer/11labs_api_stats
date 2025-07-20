# ElevenLabs Credit Usage Analyzer

A Python tool that helps you understand how your ElevenLabs API credits are being used. This script retrieves detailed information about all your API calls within a specific time period and provides comprehensive usage statistics.

## What This Tool Does

- 📊 **Analyzes your credit usage** - See exactly how many credits each API call consumed
- 🗣️ **Tracks speech generation** - Monitor text-to-speech API calls and their costs
- 💬 **Monitors conversational AI** - Track usage of ElevenLabs' conversational AI features
- 📈 **Provides detailed reports** - Get breakdowns by voice, source, call type, and time
- 💾 **Saves results automatically** - Creates timestamped JSON files with all data
- 📋 **Shows subscription info** - Displays your current plan limits and usage

## Prerequisites

Before using this tool, you'll need:

1. **Python 3.7 or newer** installed on your computer
2. **An ElevenLabs account** with API access
3. **Your ElevenLabs API key** (found in your ElevenLabs dashboard) --> **This needs to have sufficient permissions.**

## Installation

1. **Clone or download this repository**

   ```bash
   git clone <repository-url>
   cd <into the repo named folder>
   ```

2. **Install the required Python package**

   ```bash
   pip install elevenlabs
   ```

## Setup

### Getting Your API Key

1. Log into your [ElevenLabs account](https://elevenlabs.io)
2. Go to your Profile settings
3. Find your API key in the API section
4. Copy the key (it looks like `sk-...`)

### Setting Your API Key

You need to tell the script your API key using an environment variable:

**On macOS/Linux:**

```bash
export ELEVEN_API_STATS="your-api-key-here"
```

**On Windows (Command Prompt):**

```cmd
set ELEVEN_API_STATS=your-api-key-here
```

**On Windows (PowerShell):**

```powershell
$env:ELEVEN_API_STATS="your-api-key-here"
```

> 💡 **Tip:** Replace `your-api-key-here` with your actual API key from ElevenLabs

## Usage

### Basic Usage

The script needs two pieces of information:

- **Start time** - When to begin analyzing (Unix timestamp)
- **End time** - When to stop analyzing (Unix timestamp)

```bash
python credits.py <start_timestamp> <end_timestamp>
```

### Understanding Unix Timestamps

Unix timestamps are a way computers measure time - they count seconds since January 1, 1970. Don't worry, there are easy ways to get them:

**Online converters:**

- Search for them...

**Common examples:**

- `1640995200` = January 1, 2022 00:00:00 UTC
- `1672531200` = January 1, 2023 00:00:00 UTC

### Real Examples

**Analyze usage for the last 24 hours:**

```bash
# First, get yesterday's timestamp (you can use online tools)
python credits.py 1672444800 1672531200
```

**Analyze usage for a specific week:**

```bash
python credits.py 1672531200 1673136000
```

### Advanced Options

**Save to a specific file:**

```bash
python credits.py 1672531200 1673136000 --output my_usage_report.json
```

**Pretty-print the JSON output:**

```bash
python credits.py 1672531200 1673136000 --pretty
```

**Show only summary (not individual calls):**

```bash
python credits.py 1672531200 1673136000 --summary-only
```

## Understanding the Output

The tool creates several files and shows information in your terminal:

### Files Created

1. **Automatic file:** `api_stats_<timestamp>.json` - Always created with full data
2. **Custom file:** Your chosen filename (if you use `--output`)

### What's in the Reports

**Summary Information:**

- Total number of API calls made
- Total credits consumed
- Breakdown by type (speech generation vs conversational AI)
- Usage by voice, source, and time period

**Individual Call Details:**

- Exact timestamp of each API call
- Credits used per call
- Text that was converted to speech
- Voice used
- Model and settings
- Request IDs for tracking

**Subscription Information:**

- Your current plan tier
- Characters used vs limit
- Next billing cycle reset date
- Voice slots used

### Example Output

```json
{
  "summary": {
    "total_api_calls": 15,
    "total_credits_used": 1250,
    "breakdown_by_type": {
      "speech_generation": {
        "count": 12,
        "credits": 800
      },
      "conversational_ai": {
        "count": 3,
        "credits": 450
      }
    }
  }
}
```

## Common Issues & Solutions

### "API key not set" Error

**Problem:** You see `❌ Error: ELEVEN_API_STATS environment variable not set`
**Solution:** Make sure you've set your API key as shown in the Setup section

### "Permission denied" Error

**Problem:** Can't run the script
**Solution:** Make sure Python is installed and the script is executable:

```bash
chmod +x credits.py  # On macOS/Linux
```

### "Module not found" Error

**Problem:** Missing the ElevenLabs package
**Solution:** Install it with:

```bash
pip install elevenlabs
```

### No Data Returned

**Problem:** The script runs but shows 0 API calls
**Solutions:**

- Check that your timestamps cover the right time period
- Verify you have API usage during that time period
- Make sure you're using the correct API key

## Security Note

Your API key is sensitive information. Never share it publicly or include it in screenshots. The script only uses your API key to fetch your own usage data from ElevenLabs.
