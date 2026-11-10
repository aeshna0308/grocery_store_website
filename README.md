# 🛒 Grocery Store Website

A simple online grocery shopping website built using **Python Flask, SQLite, HTML, CSS, and Bootstrap-style responsive design**.

This project helps a local grocery store sell products online. Customers can browse products, add items to their cart, place orders, and choose a payment method.

## ✨ Features

### Customer Features
- View grocery products.
- View product images and prices.
- See discounted prices.
- Add products to cart.
- Increase or decrease product quantities.
- Remove products from cart.
- View total cart amount.
- Enter name, mobile number, and delivery address.
- Choose Cash on Delivery or UPI on Delivery.
- Place grocery orders.

### Admin Features
- Admin login.
- Add new grocery products.
- Edit product details.
- Delete products.
- Upload product images.
- Upload shop logo.
- Manage product prices and discounts.
- Manage product stock.
- View customer orders.
- Update order status.

## 🛠️ Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript

## 📁 Project Structure

```text
grocery_store_website/
│
├── app.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── cart.html
│   ├── checkout.html
│   ├── success.html
│   ├── admin_login.html
│   ├── admin.html
│   ├── product_form.html
│   └── order.html
│
└── static/
    ├── style.css
    └── uploads/
```

## 💻 Installation and Setup

### 1. Install Python

Download Python from:

https://www.python.org/downloads/

### 2. Clone the Repository

```bash
git clone https://github.com/aeshna0308/grocery_store_website.git
```

### 3. Open the Project Folder

```bash
cd grocery_store_website
```

### 4. Install Required Packages

```bash
pip install -r requirements.txt
```

### 5. Run the Website

```bash
python app.py
```

### 6. Open in Your Browser

```text
http://127.0.0.1:5000
```

## 🔐 Admin Login

For the initial demo setup:

- Username: `admin`
- Password: `ChangeMe123!`

**Important:** Change the default admin credentials and Flask secret key before deploying the website publicly. Configure credentials through environment variables.

## 💳 Payment Methods

The demo supports:
- Cash on Delivery
- UPI on Delivery

Note: This project does not currently include an online payment gateway. UPI on Delivery is only a payment selection, not an integrated payment transaction.

## 🚀 Future Improvements

- Online payment gateway integration.
- Customer registration and login.
- Live order tracking.
- Delivery partner application.
- WhatsApp order notifications.
- Product search and filters.
- Delivery charges and minimum order amount.
- Persistent database and image storage.
- Mobile-friendly customer experience.

## ⚠️ Important Deployment Notes

This project is a beginner-friendly demo and is not yet production-ready.

Before accepting real customer orders:
- Secure the admin login.
- Add CSRF protection and input validation.
- Use HTTPS.
- Configure persistent database and image storage.
- Back up customer orders.
- Add a privacy policy and appropriate data protection measures.

## 👩‍💻 Project Purpose

This project is created to help a local grocery shop start selling groceries online and build its own digital shopping platform.

---

**Built with ❤️ using Python Flask**
