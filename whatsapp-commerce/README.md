# Multi-Tenant WhatsApp E-Commerce Platform

A production-ready, scalable Flask multi-tenant e-commerce backend integrated with Meta WhatsApp Cloud API and Paystack payment gateway.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Quickstart Setup](#quickstart-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database & Migrations](#database--migrations)
6. [Interactive Swagger API Documentation](#interactive-swagger-api-documentation)
7. [WhatsApp Cloud API Setup Guide](#whatsapp-cloud-api-setup-guide)
8. [Paystack Payment Setup Guide](#paystack-payment-setup-guide)
9. [Running Tests](#running-tests)
10. [Project Structure](#project-structure)

---

## Architecture Overview

This project is built using a modular micro-monolith structure with Flask. It is designed for multi-tenant SaaS operations:

* **Tenant Isolation**: Workspaces (`Business`) isolate customers, products, orders, and payment configurations. Routes verify membership and role-based access control (`OWNER`, `ADMIN`, `MANAGER`, `STAFF`) via the `@require_tenant` decorator and custom SQLAlchemy query validation (`TenantQuery`).
* **WhatsApp Cloud API Integration**: Handles webhooks verification (`GET`), message events (`POST`), and automated routing to business workspaces based on receiver phone number configuration.
* **Payment Settlement Gateway**: Supports manual payment recording and automated Paystack webhook settlement with multi-tenant subaccounts.
* **Interactive API Spec**: Powered by `Flasgger` (OpenAPI / Swagger 2.0) with built-in JWT Bearer header authentication.

---

## Prerequisites

* **Python 3.10+** (Python 3.12 recommended)
* **pip** package manager
* **Virtualenv** (optional but recommended)

---

## Quickstart Setup

1. **Clone the Repository & Navigate to Workspace**:
   ```bash
   cd whatsapp-commerce
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment File Setup**:
   Copy `.env.example` to `.env` (or set environment variables):
   ```bash
   cp .env.example .env
   ```

5. **Run Database Migrations / Initialize DB**:
   ```bash
   flask db upgrade
   ```

6. **Start the Flask Development Server**:
   ```bash
   python wsgi.py
   # Or using flask CLI:
   # flask run --port 5000
   ```
   The backend will start at `http://127.0.0.1:5000`.

---

## Environment Configuration

Configure the following environment variables in `.env` or in your hosting provider configuration:

| Variable | Default Value | Description |
|---|---|---|
| `FLASK_CONFIG` | `development` | Environment mode (`development`, `production`, `testing`). |
| `SECRET_KEY` | `dev-secret-key-...` | Flask app secret key for session/security. |
| `JWT_SECRET_KEY` | `dev-jwt-secret-...` | JWT signing secret key. |
| `DATABASE_URL` | `sqlite:///instance/app.db` | Database connection URI (SQLite, PostgreSQL, etc.). |
| `WHATSAPP_VERIFY_TOKEN` | `dev-verify-token` | Verification token for WhatsApp Cloud API webhook handshake. |

---

## Interactive Swagger API Documentation

Interactive Swagger UI is integrated into the Flask app via Flasgger:

* **Swagger UI URL**: [http://127.0.0.1:5000/api/docs](http://127.0.0.1:5000/api/docs)
* **OpenAPI Spec (JSON)**: `http://127.0.0.1:5000/api/docs.json`

### Using JWT Authentication in Swagger UI:
1. Register or log in via `POST /api/v1/auth/register` or `POST /api/v1/auth/login`.
2. Copy the returned `access_token`.
3. Click the **Authorize** button at the top right of Swagger UI.
4. Enter `Bearer <your_token_here>` in the Value box and submit.
5. Provide your business workspace ID in the `X-Business-ID` header field when testing tenant-protected endpoints.

---

## WhatsApp Cloud API Setup Guide

To integrate WhatsApp messaging and automated order handling for businesses:

### 1. Facebook Developer Setup
1. Go to Meta for Developers ([developers.facebook.com](https://developers.facebook.com)) and create an app with type **Business**.
2. Add the **WhatsApp** product to your Meta app.
3. Obtain your **Phone Number ID**, **WhatsApp Business Account ID (WABA ID)**, and **Permanent User Access Token**.

### 2. Connect Business Workspace to WhatsApp Cloud API
Call the API endpoint to store WhatsApp credentials for a workspace:
```http
POST /api/v1/channels/whatsapp/connect
Header: Authorization: Bearer <JWT_TOKEN>
Header: X-Business-ID: <BUSINESS_ID>
Content-Type: application/json

{
  "phone_number_id": "10060934654321",
  "display_phone_number": "+233200000001",
  "waba_id": "900800700600",
  "access_token": "EAAG...",
  "webhook_verify_token": "custom-tenant-verify-token"
}
```

### 3. Configure Webhook Endpoint in Meta App Dashboard
1. Set Webhook URL: `https://your-domain.com/api/v1/webhooks/whatsapp`
2. Set Verify Token: Match the value of `WHATSAPP_VERIFY_TOKEN` from your `.env`.
3. Subscribe to webhook fields: `messages`.

---

## Paystack Payment Setup Guide

To enable online payment processing and automated settlement:

### 1. Obtain Paystack Credentials
1. Sign up on [paystack.com](https://paystack.com) and navigate to **Settings > API Keys & Webhooks**.
2. Copy your **Public Key** (`pk_test_...` or `pk_live_...`) and **Secret Key** (`sk_test_...` or `sk_live_...`).

### 2. Save Business Payment Gateway Settings
```http
POST /api/v1/payments/config
Header: Authorization: Bearer <JWT_TOKEN>
Header: X-Business-ID: <BUSINESS_ID>
Content-Type: application/json

{
  "provider": "PAYSTACK",
  "public_key": "pk_test_xxx",
  "secret_key": "sk_test_xxx",
  "subaccount_code": "ACCT_xxx",
  "is_active": true
}
```

### 3. Set Webhook URL in Paystack Dashboard
1. Go to Paystack Dashboard > **Settings > API Keys & Webhooks**.
2. Set Webhook URL: `https://your-domain.com/api/v1/webhooks/payments/paystack`
3. When a customer completes payment, Paystack sends a `charge.success` event to this endpoint, automatically settling the order.

---

## Running Tests

Run unit and integration tests using `pytest`:

```bash
# Ensure PYTHONPATH includes the current directory
PYTHONPATH=. pytest

# Or run specific test modules
PYTHONPATH=. pytest tests/test_auth.py
PYTHONPATH=. pytest tests/test_tenant_isolation.py
```

---

## Project Structure

```
whatsapp-commerce/
├── app/
│   ├── auth/           # Authentication endpoints & services
│   ├── businesses/     # Workspace management & RBAC
│   ├── core/           # Middlewares, permissions & Tenant query checkers
│   ├── customers/      # Customer management
│   ├── orders/         # Order lifecycle & inventory management
│   ├── payments/       # Payment records & Gateway integrations
│   ├── products/       # Products, categories & stock tracking
│   ├── webhooks/       # WhatsApp & Paystack webhook handlers
│   ├── whatsapp/       # WhatsApp channel integrations
│   ├── __init__.py     # Flask App Factory & Flasgger configuration
│   ├── config.py       # Environment configs
│   ├── extensions.py   # SQLAlchemy, JWT, Migrate, Swagger instances
│   ├── models.py       # Shared database models
│   └── cli.py          # CLI commands
├── tests/              # Test suite (100% passing)
├── requirements.txt    # Application dependencies
├── wsgi.py             # WSGI Entry point
└── README.md           # Documentation
```
