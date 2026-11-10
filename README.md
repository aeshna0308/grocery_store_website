# Grocery Store Website (Flask + SQLite)

## Included
- Customer product catalogue with product images, original price and optional discount price
- Add to cart, edit quantities, remove items and see total
- Checkout with name, 10-digit mobile, address and payment selection
- Owner login and dashboard
- Add/edit/delete products, upload product images, update stock and prices
- View orders and update order status

## Run locally (free)
1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (optional but recommended):
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start: `python app.py`
6. Open: http://127.0.0.1:5000

## Demo owner login
- Username: `admin`
- Password: `ChangeMe123!`

Change the default credentials before deployment. You can set environment variables:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SECRET_KEY` (use a long random secret)
- `SHOP_NAME`

Windows PowerShell example:
`$env:ADMIN_USERNAME="youradmin"; $env:ADMIN_PASSWORD="your-strong-password"; $env:SECRET_KEY="a-long-random-secret"; $env:SHOP_NAME="Your Shop Name"; python app.py`

## Important before going public
This is a learning/demo starter, not a production-hardened store. It uses SQLite and local image storage. Before public launch, add CSRF protection, HTTPS, proper admin password hashing stored in a database, backups, rate limiting, order notifications, privacy policy, and production hosting. UPI on delivery is only a selected payment option; no online payment gateway is connected. Do not collect card/UPI PIN details on this site. Use a payment gateway provider for actual online payments.

Upload your shop logo from Owner dashboard > Shop logo. It appears beside the shop name in the website header.
