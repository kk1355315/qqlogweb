# Project: QQ Database Decryption Tools

## Overview
This workspace contains tools, scripts, and documentation dedicated to decrypting the SQLite databases used by Tencent QQ clients across various platforms (Windows, Android, iOS, macOS, Linux). The primary goal is to extract the SQLCipher encryption keys and process the database files (specifically `nt_msg.db` for NTQQ and `Msg3.0.db` for legacy versions) to make them readable by standard tools.

## Directory Structure
The core content resides in the `qq-win-db-key` directory:

*   **Documentation (`*.md`)**: detailed tutorials for each platform (e.g., `教程 - NTQQ (Windows).md`, `基础教程 - NTQQ 解密数据库.md`).
*   **Frida Scripts (`*.js`)**: JavaScript files used with Frida to hook into the QQ process and intercept encryption keys (e.g., `android_dump.js`, `ios_get_key.js`).
*   **Python Scripts (`*.py`)**: Utilities for key dumping, database processing, and automation (e.g., `pcqq_get_key.py`, `android_hook_md5.py`).
*   **Legacy Tools (`*.cpp`)**: C++ source code for tools targeting older PCQQ versions (e.g., `pcqq_rekey_to_none.cpp`).

## Key Workflows

### 1. Windows NTQQ Decryption (Current Focus)
The modern "New Tencent" architecture (NTQQ) requires a specific workflow:
*   **Key Extraction**: The encryption key is generated at runtime. It must be intercepted using dynamic instrumentation (Frida) by hooking the `sqlite3_key_v2` function.
*   **Database Pre-processing**: The database file (`nt_msg.db`) contains a custom 1024-byte header that obfuscates the standard SQLite header. This must be stripped before any standard tool can read the file.
*   **SQLCipher Configuration**:
    *   **Cipher**: AES-256-CBC
    *   **KDF Iterations**: 4000
    *   **HMAC Algorithm**: HMAC_SHA1
    *   **Page Size**: 4096
    *   **KDF Algorithm**: PBKDF2_HMAC_SHA512

### 2. Legacy PCQQ (Windows)
Older versions require different methods, often involving memory dumping or modifying the client to write a unencrypted database (`pcqq_rekey_to_none.cpp`).

### 3. Mobile Platforms (Android/iOS)
*   **Android**: Methods involve extracting keys from system backups or using root access with Frida hooks (`android_dump.js`).
*   **iOS**: Scripts provided for extracting keys from jailbroken devices or backups (`ios_get_key.js`).

## Development & Usage
*   **Prerequisites**:
    *   **uv**: [Project Manager](https://github.com/astral-sh/uv). All python commands are executed via `uv`.
    *   **Frida**: Installed via `uv pip install frida-tools`.
    *   **DB Browser for SQLite**: (With SQLCipher support) For viewing the decrypted data.
*   **Common Commands**:
    *   *Initialize Env*: `uv venv` then `uv pip install frida-tools`
    *   *Hook Key (Windows)*: `uv run frida -l hook_key.js -n QQ.exe`
    *   *Clean Database*: `uv run prepare_db.py`

## Current Operation: NTQQ Decryption Plan

### 1. Goal (First Principles)
Decrypt `C:\Users\1\Documents\Tencent Files\1355315664\nt_qq\nt_db\nt_msg.db` to access chat logs.

### 2. Design
*   **Step A: Get Key (Hook)**: Use Frida (`hook_key.js`) via `uv` to intercept the key from the running QQ process.
*   **Step B: Pre-process (Clean DB)**: Use Python (`prepare_db.py`) via `uv` to strip the 1024-byte header.
*   **Step C: View**: User opens the cleaned DB with the key using DB Browser for SQLite.

### 3. Execution Instructions

#### Step A: Extract Key
1.  Ensure QQ is running and logged in.
2.  Run: `uv run frida -l hook_key.js -F` (Attaches to the frontmost window/QQ).
3.  Click around in QQ to trigger DB access.
4.  Copy the output key.

#### Step B: Clean Database
1.  Run: `uv run prepare_db.py`
2.  This generates `nt_msg_clean.db` in the current directory.

#### Step C: Open Database
1.  Open `nt_msg_clean.db` in DB Browser for SQLite.
2.  Enter the key.
3.  Set settings:
    *   Page size: 4096
    *   KDF iterations: 4000
    *   HMAC algorithm: HMAC_SHA1
    *   KDF algorithm: PBKDF2_HMAC_SHA512

## Code Generation Principles (Prioritized)

1.  **First Principles**: Identify core needs (Decryption) and boundaries (OS, Tool capabilities).
2.  **YAGNI**: Only implement what is currently needed (Key extraction + Header removal).
3.  **KISS**: Keep design simple (Scripts over complex apps).
4.  **SOLID**: Modular design (Python for IO, JS for Hooking).
5.  **DRY**: Extract common logic where applicable.

*Sequential Adjustment:* Architecture/Analysis -> First Principles. Incremental Dev -> YAGNI/KISS.