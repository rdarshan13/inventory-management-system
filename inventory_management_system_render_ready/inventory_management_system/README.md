# StockPilot: Inventory Management System

A ready-to-run beginner-friendly inventory website built with Python, Flask, SQLite, HTML, CSS, and a little JavaScript.

## Features
- Dashboard cards for product count, total units, stock value, low-stock items, and out-of-stock items
- Add, edit, and delete products
- Search by product name, SKU, or supplier
- Filter by category
- Add stock or remove stock with validation
- Low-stock and out-of-stock status labels
- SQLite database created automatically with sample products
- Responsive layout for desktop and mobile

## Requirements
- Python 3.10 or newer
- Internet is not required after Flask is installed

## Run on Windows
1. Extract the ZIP file.
2. Open the extracted `inventory_management_system` folder.
3. In File Explorer, click the address bar, type `cmd`, and press Enter.
4. Run:

   ```bash
   py -m venv .venv
   .venv\\Scripts\\activate
   py -m pip install -r requirements.txt
   py app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

If `py` is unavailable, use `python` instead.

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Then visit `http://127.0.0.1:5000`.

## Database
The `inventory.db` SQLite database is created automatically the first time the app starts. Four sample products are inserted only when the database is empty. Delete `inventory.db` if you want to reset the demo data, then restart the app.

## Notes
This is a local educational project. Before deploying publicly, turn off Flask debug mode, use a strong secret key from an environment variable, and add authentication/authorization and production hosting configuration.
