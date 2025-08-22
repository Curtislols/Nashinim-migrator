import sys
from pathlib import Path
import asyncio
from fastapi import FastAPI, HTTPException
from urllib.parse import urlparse
from typing import Optional

# --- Setup and Imports ---
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from platform_detector import detect_platform
from migrator_tool import PLATFORM_MAPPING 

app = FastAPI(title="Menu Scraper API")

# --- The Single, Intelligent API Endpoint ---
@app.get("/api/v1/scrape")
async def scrape_unified(url: str, choice_id: Optional[int] = None):
    if not urlparse(url).scheme:
        raise HTTPException(status_code=400, detail="Invalid URL provided.")

    try:
        platform_name = detect_platform(url)
        if not platform_name:
            raise ValueError(f"Could not identify the platform for {url}")

        platform_config = PLATFORM_MAPPING[platform_name]
        is_interactive = platform_config.get("interactive", False)

        if is_interactive and choice_id is None:
            print(f"API JOB: Platform '{platform_name}' is interactive. Discovering choices...")
            choice_finder_func = platform_config["choice_finder"]
            choices = await choice_finder_func(url)
            return {
                "status": "choices_pending",
                "message": "This URL requires a choice. Please re-query with a 'choice_id'.",
                "choices": choices
            }
        else:
            print(f"API JOB: Running full pipeline for '{platform_name}'...")
            scraper_func = platform_config["scraper"]
            transformer_func = platform_config["transformer"]

            if is_interactive:
                raw_data = await scraper_func(url, choice_id)
            else:
                raw_data = await scraper_func(url)
            
            transformed_data = transformer_func(raw_data)
            if not transformed_data:
                raise ValueError("Transformation failed.")
            
            return {"status": "completed", "data": transformed_data}

    except Exception as e:
        safe_error_message = str(e).encode('utf-8', 'replace').decode('utf-8')
        print(f"API JOB FAILED for {url}: {safe_error_message}")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {safe_error_message}")