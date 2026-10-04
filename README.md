# Beaver's Choice Paper Company — Multi-Agent System

A multi-agent AI system that automates sales, inventory, and quoting for a
fictional paper supply company. A natural-language customer request (e.g.
*"I need 500 sheets of A4 paper for my office"*) is classified by an
orchestrator agent and routed to one of three specialist worker agents,
which check stock, apply pricing logic, and record the resulting
transaction in a SQLite database — all without human intervention.

Built with [pydantic-ai](https://ai.pydantic.dev/) for agent orchestration
and structured (Pydantic-validated) outputs, backed by OpenAI's
`gpt-4o-mini` via the Vocareum proxy.

## How it works

```
Customer request (natural language)
        │
        ▼
 Orchestrator Agent  ── classifies request as: inventory | quote | sale | unknown
        │
        ├── inventory ──► Inventory Agent  (stock levels, reorder needs, delivery estimates)
        ├── quote     ──► Quote Agent      (price lookup, bulk discount, records a sale)
        └── sale      ──► Sales Agent      (stock check, finalizes order, records a sale)
```

Each worker agent is given a focused toolset (plain Python functions
wrapping the database layer) and a system prompt describing its job. The
orchestrator never talks to the database directly — it only decides which
worker handles the request.

| Agent | Role | Tools it can call |
|---|---|---|
| `orchestrator_agent` | Classifies the incoming request | — (classification only) |
| `inventory_agent` | Answers stock/availability questions | inventory snapshot, stock level, delivery estimate, cash balance, financial report |
| `quote_agent` | Generates a priced quote, applies bulk discounts, records the sale | quote history search, stock level, delivery estimate, create transaction |
| `sales_agent` | Finalizes explicit orders | stock level, delivery estimate, create transaction, cash balance, financial report |

All three worker agents return a structured Pydantic model
(`InventoryResponse`, `QuoteResponse`, `SalesResponse`) rather than free
text, so downstream code can rely on consistent fields (e.g.
`total_price`, `needs_reorder`, `success`) instead of parsing prose.

## Data model

A SQLite database (`munder_difflin.db`) is created on first run with four
tables:

- **`inventory`** — item name, category, unit price, current stock, min
  stock level (sampled from a built-in `paper_supplies` catalog of 47
  paper types and products)
- **`transactions`** — every `stock_orders` (purchase) and `sales` event;
  cash balance and current stock are both *derived* from this table rather
  than stored directly, so they're always consistent with history
- **`quote_requests`** / **`quotes`** — historical quote data (loaded from
  CSV) that the Quote Agent searches to anchor its pricing

Bulk discounting logic (in the Quote Agent's prompt): 5% off orders of
500+ units, 10% off orders of 1000+ units.

## Setup

### 1. Install dependencies

```
pip install pandas numpy sqlalchemy python-dotenv pydantic pydantic-ai
```

### 2. Set your API key

Create a `.env` file in the project root:

```
UDACITY_OPENAI_API_KEY=your_key_here
```

(This project is configured to route requests through the Vocareum OpenAI
proxy at `https://openai.vocareum.com/v1` — change `OPENAI_BASE_URL` in
`project_starter.py` if you're using a standard OpenAI key instead.)

### 3. Provide the input CSVs

The database initializer expects three CSV files in the project root
(not included in this package):

- `quote_requests.csv` — historical quote request/response pairs
- `quotes.csv` — historical quotes, including a `request_metadata` column
  (a stringified dict with `job_type`, `order_size`, `event_type`)
- `quote_requests_sample.csv` — the test scenarios to run through the
  system (expects `request_date`, `request`, and optionally `job`,
  `event`, `need_size` columns)

### 4. Run the test scenarios

```
python project_starter.py
```

This will:
1. Initialize the database (inventory + seeded transaction history)
2. Feed every row of `quote_requests_sample.csv` through the multi-agent
   system in date order
3. Snapshot cash balance and inventory value before/after each request
4. Write a full results log to `test_results.csv`

## Output: `test_results.csv`

Each row records one processed request:

| Column | Meaning |
|---|---|
| `request_id` | Sequential request number |
| `request_date` | Date the request was made |
| `request_type` | How the orchestrator classified it (`inventory` / `quote` / `sale`) |
| `worker_name` | Which agent handled it |
| `cash_before` / `cash_after` / `cash_delta` | Cash balance change from this request |
| `inventory_value` | Total inventory value after the request |
| `fulfillment_status` | `fulfilled`, `unfulfilled`, `not_applicable`, or `unknown`, derived from keywords in the agent's response |
| `order_details` | Short summary (`size=..., event=...`) from the request's context columns |
| `response` | The agent's full natural-language answer to the customer |

## Known limitations

- **Fulfillment status is a keyword heuristic**, not a structured field
  from the agent — it scans `response_text` for phrases like "order
  confirmed" or "insufficient stock". This is fragile if an agent phrases
  things differently than expected.
- **No conversation memory** — each request is handled independently;
  agents don't see prior turns in a multi-message exchange.
- **Pricing/discount rules live in the system prompt**, not in code —
  the LLM is trusted to apply the 5%/10% discount thresholds correctly
  rather than it being enforced programmatically.
- **`time.sleep(1)` between requests** in the test harness — a simple
  rate-limit safeguard, not required for correctness.

## Project structure

```
.
├── project_starter.py          # Database layer, tools, agents, test harness
├── munder_difflin.db           # SQLite DB (created on first run)
├── quote_requests.csv          # Historical quote requests (not included)
├── quotes.csv                  # Historical quotes (not included)
├── quote_requests_sample.csv   # Test scenarios (not included)
├── test_results.csv            # Output log from run_test_scenarios()
└── .env                        # UDACITY_OPENAI_API_KEY (not committed)
```
