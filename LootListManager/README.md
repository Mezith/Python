# 📘 Loot List Manager (Desktop App)
## 🎯 Overview
**Loot List Manager** is a desktop application for the LootListManager World of Warcraft addon.
It synchronizes your Google Spreadsheet with the addon’s `LootListManager.lua` SavedVariables file, allowing you to:

- Download spreadsheet data into the addon

- Manually update the spreadsheet from the addon

- Automatically live‑update the spreadsheet whenever the Lua file changes

This tool is designed for guilds or raid leaders who maintain loot priority lists, attendance sheets, or DKP‑style systems in Google Sheets.

The application is built with:

- Python 3.11

- CustomTkinter (modern UI)

- Google Sheets API

- Pandas / NumPy for data processing

## ✨ Features
### 🔄 Two‑way synchronization
- Download → Addon  
Pulls data from Google Sheets and overwrites the Lua file.

- Upload → Google Sheets  
Reads the Lua file and updates the spreadsheet.

## ⚡ Live Update Mode
Watches the Lua file for changes and automatically pushes updates to Google Sheets.

## 🧠 Smart Strikethrough Sync
The app detects strikethrough formatting in Google Sheets and mirrors it in the Lua file (and vice‑versa).

## 💾 Persistent Configuration
The app remembers:

- Last used Lua file path

- Spreadsheet ID

- Sheet name

- Column range

Stored in the `Config/` folder.

## 🎨 Modern UI
- CustomTkinter interface

- Background image

- Tooltips

- Resizable layout

## 📦 Requirements
### Python
- Python 3.11 (recommended)

### Python packages
Install via:
```
pip install -r requirements.txt
```
### Google API Credentials
You must include:

```
images/credentials.json
```
This file identifies the *Google Cloud project* — users authenticate with their own Google accounts, so this is safe to distribute.


The app will generate:

```
images/token.json
```
after the user logs in.

### WoW Addon
You must install the LootListManager addon and load it in game so the Lua file exists:

```
World of Warcraft\_classic_\WTF\Account\<AccountName>\<Server>\<Character>\SavedVariables\LootListManager.lua
```
## 🚀 Installation
### 1. Download Everything withing LootListManager

### 2. Install dependencies
```
pip install -r requirements.txt
```
### 3. Run the application
```
python lootlist_manager_app.py
```
## 🖥️ Usage Guide
### 1. Select your Lua file
Click Choose File Path and select:

```
LootListManager.lua
```
### 2. Enter Google Spreadsheet details
- Spreadsheet ID  
From the URL:
`https://docs.google.com/spreadsheets/d/<ID>/edit`

- Sheet Name  
Example: `Sheet1`

- Column Range  
Example: `A:AC`

### 3. Choose an action
📥 Download
Pulls data from Google Sheets → writes to Lua file.

📤 Manual Update
Reads Lua file → updates Google Sheets.

🔁 Live Update
Watches the Lua file for changes and pushes updates automatically.

## 🧩 Project Structure
```
LootListManager-Desktop/
│
├── lootlist_manager_app.py
├── requirements.txt
├── README.md
│
├── images/
│   ├── icon.ico
│   ├── bckrnd.png
│   └── credentials.json
│
└── Config/
   ├── config1.txt
   ├── config2.txt
   ├── config3.txt
   ├── config4.txt
   └── config5.txt (runtime only)
```

## 🔐 About Google Credentials
The `credentials.json`:

- Identifies the Google Cloud project

- It is safe to distribute and required for OAuth desktop apps

Users authenticate with their own Google accounts.
