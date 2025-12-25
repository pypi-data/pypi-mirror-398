# Flightline CLI: Technical Deep Dive & Functional Summary

This document serves as a comprehensive technical summary of the Flightline CLI tool. It is intended to provide Large Language Models (LLMs) and technical writers with the detailed context needed to generate accurate marketing copy, documentation, and case studies.

## 1. Executive Summary

Flightline is a **privacy-first synthetic data generator**. It solves the problem of "we need realistic test data, but we can't use production data due to privacy concerns."

Unlike traditional Faker libraries that require writing code to define schemas, Flightline uses a **"Learn & Replicate"** architecture. It reads your actual data files, learns their structure and business rules using an LLM, and creates a "Data Profile" (blueprint). This profile is then used to manufacture unlimited quantities of statistically similar but completely fake data.

## 2. Core Workflow

The workflow consists of two distinct commands that separate **Analysis** from **Generation**.

```mermaid
graph LR
    A[Real Data (Sensitive)] -->|flightline learn| B(Data Profile);
    B -->|flightline generate| C[Synthetic Data (Safe)];
    B -->|flightline generate| D[Synthetic Data (Safe)];
    style A fill:#ff9999,stroke:#333,stroke-width:2px
    style B fill:#ffff99,stroke:#333,stroke-width:2px
    style C fill:#99ff99,stroke:#333,stroke-width:2px
    style D fill:#99ff99,stroke:#333,stroke-width:2px
```

## 3. Detailed Functionality

### Phase 1: The `learn` Command

**Command:** `flightline learn <path/to/sample.json>`

**Purpose:** To extract the "DNA" of a dataset without retaining any of the actual "cells" (values).

**Mechanism:**
1.  **Ingestion:** The CLI reads the target file.
    *   *Smart Truncation:* If the file is massive, it intelligently truncates it (e.g., to 50k characters) to fit within the LLM's context window while retaining enough records to establish a pattern.
2.  **Analysis (LLM-Driven):** The sample is sent to an LLM (default `google/gemini-3-flash-preview` via OpenRouter) with a specialized system prompt acting as a "Data Analyst Expert."
3.  **Extraction:** The LLM identifies:
    *   **Schema Structure:** Nested objects, arrays, and field hierarchy.
    *   **Data Types:** `string`, `float`, `boolean`, `ISO8601 date`, etc.
    *   **Business Rules:** Implicit logic (e.g., `tax_amount` = `subtotal` * `tax_rate`, or `shipped_at` must be > `created_at`).
    *   **PII Detection:** It flags fields like `email`, `phone`, `address`, and names.
    *   **Patterns:** Regex-like formats (e.g., Order IDs follow `ORD-YYYY-XXXX`).

**Output:** A `profile.json` file.
*   **Crucial Security Feature:** This file contains **ZERO** real data values. It is purely metadata. You can safely email this profile to an external contractor or upload it to a public repo without leaking customer data.

### Phase 2: The `generate` Command

**Command:** `flightline generate -n <count>` (Alias: `flightline gen`)

**Purpose:** To mass-produce high-fidelity data based on the profile.

**Mechanism:**
1.  **Blueprint Loading:** Reads the `profile.json` created in Phase 1.
2.  **Parallel Execution:**
    *   The CLI calculates how many batches are needed (default 10 records per batch).
    *   It spins up a Python `ThreadPoolExecutor`.
    *   Multiple requests are sent to the LLM simultaneously to generate data in parallel, drastically reducing wait times.
3.  **Synthesis:**
    *   The LLM receives the Profile + a specific count (e.g., "Generate 10 records").
    *   It "hallucinates" valid data that strictly adheres to the schema.
    *   **PII Handling:** It invents realistic names, addresses, and emails that look real but don't exist.
    *   **Logic Enforcement:** It ensures the business rules (e.g., math, dates) defined in the profile are respected.
4.  **Assembly:** The batches are collected, flattened into a single list, and saved to a timestamped file (e.g., `synthetic_20241125.json`).

### The Interface: "HUD" (Heads-Up Display)

Flightline features a distinctive terminal UI inspired by military aircraft Multi-Function Displays (MFDs).

*   **Aesthetics:** High-contrast Phosphor Green text on a black background.
*   **Visual Language:**
    *   `[SYS RDY]`: System Ready
    *   `WP01` / `WP02`: Waypoints (steps in the process)
    *   `ACT`: Active status
    *   `CMPLT`: Complete
*   **Live Dashboard:** During generation, it renders a real-time table showing the status of every parallel batch (Pending, Active, Complete), an overall progress bar, and an ETA timer.

---

## 4. Explicit Example: "Customer Orders"

To illustrate exactly how it works, let's look at a concrete example using an e-commerce dataset. This example uses real outputs from the Flightline CLI.

### A. The Input (`samples/customer_orders.json`)
*Real production data (sensitive).*

```json
[
  {
    "order_id": "ORD-2024-00147",
    "customer": {
      "id": "CUST-8829",
      "first_name": "Sarah",
      "last_name": "Mitchell",
      "email": "sarah.mitchell@gmail.com",  // <--- PII
      "phone": "+1-555-234-8891",             // <--- PII
      "address": {
        "street": "1847 Oak Valley Drive",
        "city": "Austin",
        "state": "TX",
        "zip": "78701"
      }
    },
    "items": [
      {
        "sku": "LAPTOP-PRO-15",
        "name": "ProBook Laptop 15\"",
        "quantity": 1,
        "unit_price": 1299.99
      },
      {
        "sku": "USB-C-DOCK",
        "name": "USB-C Docking Station",
        "quantity": 1,
        "unit_price": 189.99
      }
    ],
    "subtotal": 1489.98,
    "tax_rate": 0.0825,
    "tax_amount": 122.92,
    "total": 1612.90,
    "status": "shipped",
    "created_at": "2024-11-20T14:32:18Z",
    "updated_at": "2024-11-21T09:15:44Z",
    "shipped_at": "2024-11-21T09:15:44Z"
  }
]
```

### B. The Learn Process
User runs:
```bash
flightline learn samples/customer_orders.json
```

Flightline analyzes the file and produces:

### C. The Profile (`flightline_output/profile.json`)
*Metadata only (safe).*

```json
{
  "schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "order_id": { "type": "string" },
        "customer": {
          "type": "object",
          "properties": {
            "first_name": { "type": "string" },
            "email": { "type": "string" },
            // ... nested objects ...
          }
        },
        "subtotal": { "type": "number" },
        "total": { "type": "number" }
      }
    }
  },
  "patterns": {
    "order_id": "Prefix 'ORD-' followed by 4-digit year then hyphen then numeric sequence (e.g., ORD-YYYY-NNNNN).",
    "customer.id": "Prefix 'CUST-' followed by numeric identifier (e.g., CUST-####)."
  },
  "business_rules": [
    "total should equal subtotal + tax_amount (rounded to currency precision).",
    "If status is 'processing', shipped_at is expected to be null.",
    "created_at <= updated_at."
  ],
  "pii_fields": [
    "customer.first_name",
    "customer.email",
    "customer.phone",
    "customer.address.street"
  ],
  "example_formats": {
    "order_id": "ORD-YYYY-NNNNN (e.g., 'ORD-2025-00001' format; do not use real values)",
    "customer.email": "user@domain.tld (standard email format)"
  }
}
```

### D. The Generate Process
User runs:
```bash
flightline gen -n 50
```

Flightline uses the profile to create 50 brand new records.

### E. The Output (`flightline_output/synthetic_....json`)
*Fake data (safe).*

```json
[
  {
    "order_id": "ORD-2025-00001",
    "customer": {
      "id": "CUST-1001",
      "first_name": "Avery",
      "last_name": "Mendoza",
      "email": "avery.mendoza@examplemail.com",
      "phone": "+1-415-555-0132",
      "address": {
        "street": "221 Embarcadero St Apt 5B",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94107"
      }
    },
    "items": [
      {
        "sku": "PROD-XL-001",
        "name": "Wireless Headphones",
        "quantity": 1,
        "unit_price": 129.99
      }
    ],
    "subtotal": 168.99,
    "tax_rate": 0.0875,
    "tax_amount": 14.79,
    "total": 183.78,                        // Math is correct (168.99 + 14.79 = 183.78)
    "status": "processing",
    "created_at": "2025-03-10T09:15:00Z",
    "shipped_at": null                      // Correct logic: processing = no ship date
  }
]
```

### 6. CLI Experience (Terminal Output)

The Flightline CLI provides a unique, high-contrast MFD (Multi-Function Display) interface. Below are the actual outputs from a session.

#### The Learn Command

```text
$ flightline learn samples/customer_orders.json

                            ║
                            ║
                       ╔════╩════╗
                       ║         ║
            ═══════════╣         ╠═══════════
                       ║         ║
                       ╚═════════╝

███████╗██╗     ██╗ ██████╗ ██╗  ██╗████████╗██╗     ██╗███╗   ██╗███████╗
██╔════╝██║     ██║██╔════╝ ██║  ██║╚══██╔══╝██║     ██║████╗  ██║██╔════╝
█████╗  ██║     ██║██║  ███╗███████║   ██║   ██║     ██║██╔██╗ ██║█████╗  
██╔══╝  ██║     ██║██║   ██║██╔══██║   ██║   ██║     ██║██║╚██╗██║██╔══╝  
██║     ███████╗██║╚██████╔╝██║  ██║   ██║   ███████╗██║██║ ╚████║███████╗
╚═╝     ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝

                              flightline learn

╔══════════════════════════════════════════════════════════════╗
║  SYNTHETIC DATA GENERATOR                                    ║
║  COMMAND: LEARN                                              ║
║                                               [SYS RDY] 0341Z║
╚══════════════════════════════════════════════════════════════╝

     STATUS: ◉ [RDY] STARTING

WP01 ─╼ INPUT: CUSTOMER_ORDERS.JSON
     ► MODEL: GOOGLE/GEMINI-3-FLASH-PREVIEW

     ◉── LEARNING COMPLETE

┌──────────────────────────────────────────────────┐
│  ◉──◉ DONE ◉──◉                                  │
│  ────────────────────────────────────────────────│
│  PROFILE: PROFILE.JSON                           │
│  OUTPUT: FLIGHTLINE_OUTPUT                       │
│  FIELDS: 2                                       │
│  PII FIELDS: 9                                   │
│  RULES: 13                                       │
│                                     [CMPLT] 0341Z│
└──────────────────────────────────────────────────┘

     ► NEXT: RUN [FLIGHTLINE GENERATE -N 100] TO CREATE SYNTHETIC DATA
```

#### The Generate Command

```text
$ flightline generate -n 100

                              flightline generate

╔══════════════════════════════════════════════════════════════╗
║  SYNTHETIC DATA GENERATOR                                    ║
║  COMMAND: GENERATE                                           ║
║                                               [SYS RDY] 0341Z║
╚══════════════════════════════════════════════════════════════╝

     STATUS: ◉ [RDY] STARTING

WP01 ─╼ PROFILE: FLIGHTLINE_OUTPUT/PROFILE.JSON
WP02 ─╼ OUTPUT: FLIGHTLINE_OUTPUT
     ► MODEL: GOOGLE/GEMINI-3-FLASH-PREVIEW
     ► COUNT: 100

     STATUS: ◉ [ACT] LOADING PROFILE
     ◉── PROFILE LOADED

╔════════════════════════════════════════════════════════════╗
║  REC GEN   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓        100%║
║  [✓][✓][✓][✓][✓][✓][✓][✓][✓][✓]                            ║
║  COUNT: 100/100    ETA: 00:00                       [CMPLT]║
╚════════════════════════════════════════════════════════════╝

     ◉── GENERATED 100 RECORDS

     STATUS: ◉ [ACT] WRITING OUTPUT
     ◉── SAVED

┌──────────────────────────────────────────────────┐
│  ◉──◉ DONE ◉──◉                                  │
│  ────────────────────────────────────────────────│
│  RECORDS: 100                                    │
│  FILE: SYNTHETIC_20251206_194231.JSON            │
│  OUTPUT: FLIGHTLINE_OUTPUT                       │
│                                     [CMPLT] 0342Z│
└──────────────────────────────────────────────────┘
```

## 5. Technical Differentiators for Marketing

1.  **"Zero-Touch" Configuration:** No need to write Python scripts, regex, or config files manually. Point it at a file, and it learns.
2.  **Context-Aware:** Unlike simple randomizers, Flightline understands *relationships*. It won't generate a `shipped_at` date that is before the `created_at` date because the LLM understands the concept of time in shipping.
3.  **Developer Experience:** The CLI is built for speed. The parallel batching means generating 1,000 complex records happens in seconds/minutes, not hours.
4.  **Local-First / Private:** The "Learn" step can happen on a developer's machine. The sensitive data never needs to leave the secure environment if using a local LLM (though default configuration uses OpenRouter).

