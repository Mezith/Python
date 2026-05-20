# 📘 README.md — Costco Product Availability Webscraper
## 🕷️ Overview
The Costco Webscraper is a desktop automation tool designed to monitor product availability on Costco’s website.
It uses **undetected‑chromedriver**, **Selenium**, and a lightweight **CustomTkinter GUI** to repeatedly check a product’s status and notify you the moment it becomes available.

This scraper is ideal for:

- High‑demand items

- Restock alerts

- Automated product monitoring

- Avoiding manual refreshing

The scraper simulates realistic browsing behavior, scrolls the page, hovers elements, and waits between checks to reduce detection.

## ✨ Features
### 🔍 Real‑Time Product Monitoring
- Checks a product’s status using a user‑defined XPath

- Reads any attribute (e.g., button text, class, aria-label)

- Detects “Add to Cart” or any custom value

### 🧠 Human‑like Behavior Simulation
- Scrolls the page gradually

- Randomized mouse movement

- Hover interactions

- Randomized sleep intervals

- Reduces bot detection

### 🔔 Desktop Notifications
- Windows toast notifications when the product becomes available

- Optional sound alert (Time.wav)

### 💾 Persistent Configuration
Automatically saves and loads:

- Product URL

- XPath

- Attribute to read

- Sleep range (start/end seconds)

Stored in:

```
scraper_config.json
```
### 🖥️ Modern GUI
- Built with CustomTkinter:

- Clean interface

- Dark/light mode support

- Start/Stop button

- Status indicator

- Input placeholders

### 📸 Automatic Screenshots
On errors, the scraper captures screenshots and saves them to:

```
Screenshots/
```
### 📝 Logging
All console output is logged to:

```
Logs/costco_log.txt
```
### 📦 Requirements
### Python
- Python 3.10+ recommended

- Windows 10/11 (due to toast notifications and winsound)

### Dependencies
Install everything with:

```
pip install -r requirements.txt
```
Your requirements file should include:

```
undetected-chromedriver
selenium
customtkinter
win10toast
```

### Chrome Browser
You must have Google Chrome installed at:

## 🚀 Usage
### 1. Run the scraper
```
python scraper.py
```
### 2. Fill in the fields
Product URL
Example:

```
https://www.costco.ca/some-product.html
```
XPath
Example:

```
//*[@id="add-to-cart-btn"]
```
Attribute
Example:

```
innerText
```
Sleep Range
How long to wait between checks:

- Start: 30

- End: 90

The scraper will randomly pick a value between these numbers.

## ▶️ Start Scraping
Click Start Scraping.

The scraper will:

1. Launch undetected Chrome

2. Load the product page

3. Scroll and simulate human behavior

4. Check the element’s attribute

5. If the value matches “Add to Cart”:

  - Play a sound
  
  - Show a toast notification
  
  - Log the event
  
  - Stop the scraper

## 🛑 Stop Scraping
Click Stop Scraping at any time.

The scraper will:

- Stop the loop

- Close Chrome

- Save your settings

- Restore stdout

## 💾 Configuration File
The scraper automatically saves your inputs to:

```
scraper_config.json
```
json Example:

```
{
    "url": "https://www.costco.ca/example.html",
    "xpath": "//*[@id='add-to-cart-btn']",
    "attribute": "innerText",
    "sleep_start": 30,
    "sleep_end": 90
}
```
This file loads automatically on startup.

## 📁 Project Structure
```
CostcoScraper/
│
├── scraper.py
├── scraper_config.json
├── requirements.txt
│
├── Logs/
│   └── costco_log.txt
│
└── Screenshots/
    └── screenshot_YYYY-MM-DD_HH-MM-SS.png
```

## 🧪 Troubleshooting
## ❌ Chrome fails to launch
Check your Chrome path:

```
C:\Program Files\Google\Chrome\Application\chrome.exe
```
## ❌ XPath not found
Use Chrome DevTools → Inspect → Copy XPath.

## ❌ Attribute always empty
Try:

  - `innerText`
  
  - `textContent`
  
  - `value`
  
  - `aria-label`
  
  - `class`

## ❌ Script stops immediately
Your sleep range may be invalid (e.g., empty or non‑numeric).

## 🔐 Notes on Anti‑Bot Behavior
This scraper:

- Uses undetected‑chromedriver

- Removes navigator.webdriver

- Simulates scrolling

- Simulates mouse movement

- Randomizes delays

This reduces detection but not guaranteed.
