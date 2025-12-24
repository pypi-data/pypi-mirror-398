# locknkeycmd: Secure, Zero-Knowledge Secret Management CLI

`locknkeycmd` is the official command-line interface for **LocknKey**, a secure, end-to-end encrypted secret management platform. This tool allows developers to securely inject secrets into their applications and scripts at runtime, without storing them in plain text files (specifically preventing `.env` sprawl).

## Features

*   **End-to-End Encryption**: Secrets are decrypted only in memory on your local machine.
*   **Zero-Knowledge Architecture**: The server never sees your unencrypted secrets.
*   **TOTP-Based Security**: Uses your Google Authenticator secret to derive encryption keys, adding a layer of security beyond just passwords.
*   **Environment injection**: seamlessly inject secrets into `npm start`, `python main.py`, or any other command.
*   **Multi-Environment**: Support for Development (`-d`), Staging (`-s`), and Production (`-p`) environments.

## Installation

Install via pip:

```bash
pip install locknkeycmd
```

## Prerequisites

1.  **A Lockbox/LocknKey Account**: Sign up at [https://lock-box-ashy.vercel.app](https://lock-box-ashy.vercel.app).
2.  **2FA Enabled**: You **must** enable Two-Factor Authentication (Google Authenticator) on the Web Dashboard. The CLI requires this to decrypt your vault securely.

## Quick Start

### 1. Authenticate

Log in to your account. This will open a browser window to authenticate with Google.

```bash
locknkeycmd login
```

### 2. Initialize Session (Unlock Vault)

Decrypt your master encryption key using your 2FA code. This session remains active locally so you don't need to re-enter it for every command.

```bash
locknkeycmd init
```
*Enter your 6-digit Google Authenticator code when prompted.*

### 3. Run Commands with Secrets

Inject secrets directly into your application process.

**Syntax:**
```bash
locknkeycmd run <project-name-or-id> -- <your-command>
```

**Examples:**

Run a Node.js app with **Development** secrets (Default):
```bash
locknkeycmd run my-api -- npm start
```

Run a Python script with **Production** secrets:
```bash
locknkeycmd run my-api --prod -- python main.py
```

Print secrets to console (useful for debugging/verifying):
```bash
locknkeycmd run my-api
```

## Other Commands

**Show Account Info:**
```bash
locknkeycmd --show
```

**List Organizations:**
```bash
locknkeycmd --show --org
```

**List Projects:**
```bash
locknkeycmd --show --proj
```

**Logout:**
```bash
locknkeycmd logout
```

## Security

`locknkeycmd` uses a combination of modern cryptographic primitives:
*   **Argon2id** for key derivation (hardening your TOTP secret into an encryption key).
*   **NaCl (TweetNaCl/PyNaCl)** for high-speed authenticated encryption (using XSalsa20-Poly1305).

No private keys are ever sent to the server.

## Troubleshooting

*   **"Session Locked"**: Run `locknkeycmd init` again.
*   **"Invalid Authenticator Code"**: Ensure your system time is synced.
