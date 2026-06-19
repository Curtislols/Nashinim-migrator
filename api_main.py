import sys
import os
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse
from typing import Optional
import traceback
from concurrent.futures import ProcessPoolExecutor
import inspect
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

from platform_detector import detect_platform
from migrator_tool import PLATFORM_MAPPING, MenuNotFoundError, ScrapingError, TransformationError

# --- Config from environment ---
API_KEY = os.getenv("API_KEY")  # If unset, auth is disabled (dev mode)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "3"))

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)):
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

# --- Concurrency limiter: Playwright is heavy, cap simultaneous scrapes ---
scrape_semaphore: asyncio.Semaphore

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scrape_semaphore, executor
    scrape_semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
    executor = ProcessPoolExecutor()
    yield
    executor.shutdown(wait=True)

executor: ProcessPoolExecutor

app = FastAPI(
    title="Menu Scraper API",
    description="Scrapes restaurant menus from Iranian food platforms and returns a unified JSON format.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["X-API-Key"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/v1/scrape")
async def scrape_unified(url: str, choice_id: Optional[int] = None, _=Security(verify_api_key)):
    if not urlparse(url).scheme:
        raise HTTPException(status_code=400, detail="Invalid or malformed URL provided.")

    loop = asyncio.get_running_loop()

    async with scrape_semaphore:
        try:
            platform_name = await loop.run_in_executor(executor, detect_platform, url)
            if not platform_name:
                raise ValueError(f"Could not identify the platform for '{url}'")

            platform_config = PLATFORM_MAPPING[platform_name]
            is_interactive = platform_config.get("interactive", False)

            if is_interactive and choice_id is None:
                print(f"API JOB: Platform '{platform_name}' is interactive. Discovering choices...")
                choices = await loop.run_in_executor(executor, platform_config["choice_finder"], url)
                if not choices:
                    print("API JOB: No choices found, proceeding directly to scrape.")
                else:
                    return {
                        "status": "choices_pending",
                        "message": "This URL requires a choice. Please re-query with a 'choice_id'.",
                        "choices": choices,
                    }

            print(f"API JOB: Running full pipeline for '{platform_name}'...")
            scraper_func = platform_config["scraper"]
            transformer_func = platform_config["transformer"]

            if inspect.iscoroutinefunction(scraper_func):
                raw_data = await scraper_func(url)
            elif is_interactive:
                raw_data = await loop.run_in_executor(executor, scraper_func, url, choice_id or 0)
            else:
                raw_data = await loop.run_in_executor(executor, scraper_func, url)

            transformed_data = transformer_func(raw_data)
            if not transformed_data:
                raise TransformationError("Transformer returned no data.")

            return {"status": "completed", "data": transformed_data}

        except MenuNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ScrapingError as e:
            raise HTTPException(status_code=502, detail=f"Scraper error: {e}")
        except TransformationError as e:
            raise HTTPException(status_code=500, detail=f"Transform error: {e}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Bad request: {e}")
        except Exception as e:
            tb_str = traceback.format_exc()
            print(f"UNHANDLED ERROR: {repr(e)}\n{tb_str}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {repr(e)}")