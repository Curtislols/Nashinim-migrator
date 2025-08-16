Of course. A good README file is essential for any project. Based on the tool we've built together, here is a complete README.md file that explains its purpose, structure, and usage.

You can save this text as `README.md` in the root of your project folder (`D:\Play\`).

-----

# 🚀 Restaurant Menu Migration Tool

This project is a command-line tool designed to automate the process of migrating restaurant menu data from various competitor platforms into a standardized JSON format. It handles scraping, data transformation, and image processing through a flexible, multi-stage pipeline.

The tool is built to be extensible, allowing for new competitor platforms to be added easily by creating new scraper and transformer modules.

-----

## ✨ Features

  * **Multi-Platform Scraping:** Currently supports four different menu platforms (`MeNew`, `Qbar`, `Menusaz`, and `QRMenusaz`).
  * **Modular Architecture:** Scrapers and data transformers are organized into separate modules for easy maintenance and extension.
  * **Data Transformation:** Converts disparate source data structures into a single, unified JSON format.
  * **Intelligent Price Conversion:** Uses a smart heuristic to convert various price formats (Rial, Toman, KiloToman) into a standard Toman integer.
  * **Optional Image Migration:** Includes a pipeline to download images from the source, re-upload them to your own API, and update the menu with the new URLs.
  * **Command-Line Control:** The entire process is controlled by a single, powerful command-line tool (`migrator_tool.py`).

-----

## 📁 Project Structure

The project is organized into distinct modules to separate concerns.

```
project_root/
├── scrapers/
│   ├── menewautoscraper.py
│   ├── menusazscraper.py
│   ├── qbarscraper.py
│   └── qrmenusazscraper.py
│
├── data_transformers/
│   ├── menew_transformer.py
│   ├── menusaz_transformer.py
│   ├── qbar_transformer.py
│   └── qrmenusaz_transformer.py
│
├── output/
│   ├── raw_data/          # Stores the raw JSON from scrapers
│   ├── transformed_data/  # Stores JSON after data transformation
│   └── final_data/        # Stores final JSON after image migration
│
└── migrator_tool.py       # The main controller script
```

-----

## 🔧 Setup and Installation

1.  **Clone or Download:** Place all the project files in a single directory.

2.  **Create a Virtual Environment (Recommended):**

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Dependencies:** You will need `requests` and `playwright`.

    ```bash
    pip install requests playwright
    ```

4.  **Install Playwright Browsers:** This is a required one-time setup for Playwright.

    ```bash
    playwright install
    ```

-----

## ⚙️ Configuration

Before running the full pipeline with image migration, you **must** configure your API details.

Open the `migrator_tool.py` file and edit the following placeholder variables at the top:

```python
# --- ❗️ CONFIGURATION: YOU MUST EDIT THESE TWO VALUES ---
YOUR_API_ENDPOINT = "https://api.yoursite.com/v1/images"  # <-- REPLACE THIS
YOUR_API_TOKEN = "your_secret_bearer_token_here"            # <-- REPLACE THIS
# ---------------------------------------------------------
```

The script assumes your API uses Bearer Token authentication. If it uses a different method, you may need to adjust the `headers` in the `migrate_image` function.

-----

## Usage

The entire tool is controlled from your terminal by running `migrator_tool.py` and providing the URLs you want to process as command-line arguments.

### Scrape and Transform Only

To run the pipeline without the image migration step, simply provide the URLs. The output will be saved in the `output/raw_data` and `output/transformed_data` folders.

```bash
python migrator_tool.py https://qbar.ir/manza/menu https://sowon.menusaz.com/
```

### Full Pipeline with Image Migration

To run the complete pipeline, including downloading and re-uploading all images, add the **`--with-images`** flag at the end of your command.

The final output, with the new image URLs from your system, will be saved in the `output/final_data` folder.

```bash
python migrator_tool.py https://khanehfamouri.menew.ir/catalogue --with-images
```

-----

## 🧩 Extending the Tool (Adding a New Competitor)

The modular design makes it easy to add support for a new platform.

1.  **Create a New Scraper:** Add a new file to the `scrapers/` directory (e.g., `newcompetitor_scraper.py`). It must contain a `scrape(url: str) -> dict` function.
2.  **Create a New Transformer:** Add a new file to the `data_transformers/` directory (e.g., `newcompetitor_transformer.py`). It must contain a `transform(source_data: dict) -> dict` function.
3.  **Update the Main Tool:** Open `migrator_tool.py` and add the new platform to the `if/elif` logic to recognize the new URL and call your new scraper and transformer functions.

-----

## 📄 License

This project is licensed under the MIT License.
