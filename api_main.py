import sys
from pathlib import Path
import asyncio
from fastapi import FastAPI, HTTPException
from urllib.parse import urlparse
from typing import Optional
import traceback
from concurrent.futures import ProcessPoolExecutor
import inspect

# --- Setup: Add Project Root to Python's Path ---
# This ensures that all module imports work correctly.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

# --- API Application Setup ---
app = FastAPI(
    title="Menu Scraper API",
    description="A robust API for scraping menu data from multiple platforms."
)

# --- Process Pool for Blocking Code ---
# This creates a pool of separate processes to run the slow, blocking
# Playwright scrapers without freezing the async API server.
executor = ProcessPoolExecutor()

@app.on_event("shutdown")
def on_shutdown():
    """Ensure the process pool is shut down gracefully when the API stops."""
    print("Shutting down process pool...")
    executor.shutdown(wait=True)

# --- Import Custom Logic and Mappings ---
# We import these after the path is set.
from platform_detector import detect_platform
from migrator_tool import PLATFORM_MAPPING, MenuNotFoundError, ScrapingError, TransformationError


# --- The Single, Intelligent API Endpoint ---
@app.get("/api/v1/scrape")
async def scrape_unified(url: str, choice_id: Optional[int] = None):
    """
    A single endpoint to handle all scraping requests intelligently.
    """
    if not urlparse(url).scheme:
        raise HTTPException(status_code=400, detail="Invalid or malformed URL provided.")

    loop = asyncio.get_running_loop()

    try:
        # Run the platform detector in the process pool as it may use Playwright
        platform_name = await loop.run_in_executor(executor, detect_platform, url)
        if not platform_name:
            raise ValueError(f"Could not identify the platform for '{url}'")

        platform_config = PLATFORM_MAPPING[platform_name]
        is_interactive = platform_config.get("interactive", False)
        
        # --- Interactive Logic ---
        # If the site is interactive and the user hasn't made a choice yet,
        # return the list of choices.
        if is_interactive and choice_id is None:
            print(f"API JOB: Platform '{platform_name}' is interactive. Discovering choices...")
            choice_finder_func = platform_config["choice_finder"]
            choices = await loop.run_in_executor(executor, choice_finder_func, url)

            # If no choices are found (e.g., single-location restaurant), scrape directly.
            if not choices:
                print("API JOB: No choices found, proceeding directly to scrape.")
            else:
                return {
                    "status": "choices_pending",
                    "message": "This URL requires a choice. Please re-query with a 'choice_id'.",
                    "choices": choices
                }
        
        # --- Main Pipeline Logic ---
        print(f"API JOB: Running full pipeline for '{platform_name}'...")
        scraper_func = platform_config["scraper"]
        transformer_func = platform_config["transformer"]

        # Intelligently handle both async and sync scrapers
        if inspect.iscoroutinefunction(scraper_func):
            # If the scraper is async (like Snappfood's), await it directly.
            raw_data = await scraper_func(url)
        else:
            # If the scraper is sync (like Playwright's), run it in the process pool.
            if is_interactive:
                raw_data = await loop.run_in_executor(executor, scraper_func, url, choice_id)
            else:
                raw_data = await loop.run_in_executor(executor, scraper_func, url)
        
        # The transformer is fast CPU work, so no thread/process is needed.
        transformed_data = transformer_func(raw_data)
        if not transformed_data:
            raise TransformationError("Transformer returned no data.")
        
        return {"status": "completed", "data": transformed_data}

    # --- Robust Error Handling ---
    except MenuNotFoundError as e:
        print(f"ERROR 404: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ScrapingError as e:
        print(f"ERROR 502: {e}")
        raise HTTPException(status_code=502, detail=f"Bad Gateway: A scraper-level error occurred. Details: {e}")
    except TransformationError as e:
        print(f"ERROR 500: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: Failed to transform data. Details: {e}")
    except ValueError as e: # Catches issues like invalid choice_id or bad URLs
        print(f"ERROR 400: {e}")
        raise HTTPException(status_code=400, detail=f"Bad Request: {e}")
    except Exception as e: # Generic fallback for any other unexpected error
        error_repr = repr(e)
        tb_str = traceback.format_exc()
        print(f"UNHANDLED ERROR 500: {error_repr}\n--- TRACEBACK ---\n{tb_str}\n-----------------")
        raise HTTPException(status_code=500, detail=f"An unexpected internal error occurred: {error_repr}")