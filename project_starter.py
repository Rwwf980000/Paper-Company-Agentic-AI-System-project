import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union

from sqlalchemy import create_engine, Engine

dotenv.load_dotenv()

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.
    """
    np.random.seed(seed)
    num_items = int(len(paper_supplies) * coverage)
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )
    selected_items = [paper_supplies[i] for i in selected_indices]

    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),
            "min_stock_level": np.random.randint(50, 150)
        })

    return pd.DataFrame(inventory)


def init_database(db_engine: Engine = db_engine, seed: int = 137) -> Engine:
    """
    Initialize DB with inventory, transactions, quotes, quote_requests.
    """
    try:
        # Empty transactions table schema
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],
            "units": [],
            "price": [],
            "transaction_date": [],
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        initial_date = datetime(2025, 1, 1).isoformat()

        # quote_requests
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # quotes
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # Inventory
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        initial_transactions = []

        # starting cash balance
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # one stock order per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    Insert a transaction row into DB.
    """
    try:
        date_str = date.isoformat() if isinstance(date, datetime) else date

        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise


def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Snapshot of inventory as of date.
    """
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})
    return dict(zip(result["item_name"], result["stock"]))


def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Net stock level of an item as of a date.
    """
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )


def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate supplier delivery date based on quantity.
    """
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        print(f"WARN: Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    delivery_date_dt = input_date_dt + timedelta(days=days)
    return delivery_date_dt.strftime("%Y-%m-%d")


def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Cash = sales - stock_orders up to date.
    """
    try:
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Financial report: cash, inventory value, assets, top sellers.
    """
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    cash = get_cash_balance(as_of_date)

    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Search historical quotes.
    """
    conditions = []
    params = {}

    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row) for row in result]


########################
########################
########################
# YOUR MULTI AGENT STARTS HERE (IMPLEMENTATION)
########################
########################
########################

from typing import Optional, Literal
from pydantic import BaseModel
from pydantic_ai import Agent

# Load env key for Vocareum OpenAI proxy
dotenv.load_dotenv()
UDACITY_OPENAI_API_KEY = os.getenv("UDACITY_OPENAI_API_KEY")

if not UDACITY_OPENAI_API_KEY:
    raise EnvironmentError(
        "UDACITY_OPENAI_API_KEY is not set. Put it in a .env file in this folder."
    )

# Configure environment for pydantic-ai / OpenAI
os.environ["OPENAI_API_KEY"] = UDACITY_OPENAI_API_KEY
os.environ["OPENAI_BASE_URL"] = "https://openai.vocareum.com/v1"

# pydantic-ai model identifier
MODEL_NAME = "openai:gpt-4o-mini"

# ---------- Pydantic result models ----------

class InventoryResponse(BaseModel):
    answer_text: str
    paper_type: Optional[str] = None
    requested_quantity: Optional[int] = None
    available_quantity: Optional[int] = None
    needs_reorder: bool = False
    estimated_delivery_date: Optional[str] = None


class QuoteResponse(BaseModel):
    answer_text: str
    paper_type: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    discount_applied: bool = False
    discount_reason: Optional[str] = None


class SalesResponse(BaseModel):
    answer_text: str
    success: bool
    paper_type: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None


class OrchestratorDecision(BaseModel):
    request_type: Literal["inventory", "quote", "sale", "unknown"]
    reasoning: str


class OrchestratorOutput(BaseModel):
    answer_text: str
    request_type: str
    worker_name: str


# ---------- Tool wrappers (plain functions) ----------

def tool_get_all_inventory(as_of_date: str) -> Dict[str, int]:
    return get_all_inventory(as_of_date)


def tool_get_stock_level_tool(item_name: str, as_of_date: str) -> int:
    df = get_stock_level(item_name, as_of_date)
    if df.empty:
        return 0
    return int(df["current_stock"].iloc[0])


def tool_get_supplier_delivery_date_tool(request_date: str, quantity: int) -> str:
    return get_supplier_delivery_date(request_date, quantity)


def tool_get_cash_balance_tool(as_of_date: str) -> float:
    return get_cash_balance(as_of_date)


def tool_generate_financial_report_tool(as_of_date: str) -> Dict:
    return generate_financial_report(as_of_date)


def tool_search_quote_history_tool(terms: str) -> List[Dict]:
    search_terms = [t.strip() for t in terms.split() if t.strip()]
    if not search_terms:
        search_terms = ["paper"]
    return search_quote_history(search_terms)


def tool_create_transaction_tool(
    item_name: str,
    quantity: int,
    total_price: float,
    date: str,
) -> int:
    return create_transaction(
        item_name=item_name,
        transaction_type="sales",
        quantity=quantity,
        price=total_price,
        date=date,
    )


# ---------- Worker agents ----------

inventory_agent = Agent(
    model=MODEL_NAME,
        result_type=InventoryResponse,
    tools=[
        tool_get_all_inventory,
        tool_get_stock_level_tool,
        tool_get_supplier_delivery_date_tool,
        tool_get_cash_balance_tool,
        tool_generate_financial_report_tool,
    ],
    system_prompt=(
        "You are the Inventory Agent for Beaver's Choice Paper Company.\n"
        "You answer questions about stock availability and delivery timing.\n"
        "Requests include 'Date of request: YYYY-MM-DD'. Extract that date and use it as-of.\n"
        "Use the tools to:\n"
        "- see current inventory\n"
        "- check stock level for an item\n"
        "- estimate supplier delivery date for large orders\n"
        "Explain clearly to the customer, but do NOT reveal internal costs or profit margins."
    ),
)

quote_agent = Agent(
    model=MODEL_NAME,
        result_type=QuoteResponse,
    tools=[
        tool_search_quote_history_tool,
        tool_get_stock_level_tool,
        tool_get_supplier_delivery_date_tool,
        tool_create_transaction_tool,
    ],
    system_prompt=(
        "You are the Quote Agent for Beaver's Choice Paper Company.\n"
        "You generate competitive quotes and, for this simulation, assume customers accept\n"
        "reasonable quotes immediately, so you record a 'sales' transaction.\n\n"
        "Steps:\n"
        "1. Extract paper type, quantity, and 'Date of request: YYYY-MM-DD'.\n"
        "2. Use historical quotes (tool_search_quote_history_tool) to anchor a unit price.\n"
        "3. Apply a bulk discount for large orders (e.g., 5% off for 500+, 10% off for 1000+).\n"
        "4. Compute total_price = unit_price * quantity.\n"
        "5. Record the sale using tool_create_transaction_tool.\n"
        "6. Estimate delivery using tool_get_supplier_delivery_date_tool.\n\n"
        "In answer_text, state unit price, total price, discount & reason, and delivery date.\n"
        "Do not reveal margins or internal financial details."
    ),
)

sales_agent = Agent(
    model=MODEL_NAME,
        result_type=SalesResponse,
    tools=[
        tool_get_stock_level_tool,
        tool_get_supplier_delivery_date_tool,
        tool_create_transaction_tool,
        tool_get_cash_balance_tool,
        tool_generate_financial_report_tool,
    ],
    system_prompt=(
        "You are the Sales Agent for Beaver's Choice Paper Company.\n"
        "You finalize explicit orders (e.g., 'We want to place an order').\n\n"
        "Steps:\n"
        "1. Extract paper type, quantity, and 'Date of request: YYYY-MM-DD'.\n"
        "2. Check stock via tool_get_stock_level_tool. If insufficient, explain clearly why\n"
        "   the order cannot be fully fulfilled and suggest alternatives, WITHOUT recording a sale.\n"
        "3. If stock is sufficient, compute a fair price and record a 'sales' transaction\n"
        "   with tool_create_transaction_tool.\n"
        "4. Provide an estimated delivery date using tool_get_supplier_delivery_date_tool.\n\n"
        "In answer_text, clearly state whether the order is confirmed, quantity, and total price.\n"
        "Do not reveal internal profit margins or raw DB errors."
    ),
)

# ---------- Orchestrator agent ----------

orchestrator_agent = Agent(
    model=MODEL_NAME,
    result_type=OrchestratorDecision,
    system_prompt=(
        "You are the Orchestrator Agent for Beaver's Choice Paper Company.\n"
        "Classify each incoming request as one of:\n"
        "- 'inventory': asking about availability or delivery timing.\n"
        "- 'quote': asking for prices or quotes.\n"
        "- 'sale': clearly placing or confirming an order.\n"
        "- 'unknown': anything else.\n\n"
        "Return JSON with fields:\n"
        "- request_type (inventory|quote|sale|unknown)\n"
        "- reasoning (brief explanation)."
    ),
)


def call_multi_agent_system(request_text: str) -> OrchestratorOutput:
    """
    Route a customer request through orchestrator + workers.
    """
    decision_result = orchestrator_agent.run_sync(request_text)
    decision: OrchestratorDecision = decision_result.data
    request_type = decision.request_type

    if request_type == "inventory":
        worker_name = "inventory_agent"
        worker_result = inventory_agent.run_sync(request_text)
        worker_data: InventoryResponse = worker_result.data
        answer_text = worker_data.answer_text

    elif request_type == "quote":
        worker_name = "quote_agent"
        worker_result = quote_agent.run_sync(request_text)
        worker_data: QuoteResponse = worker_result.data
        answer_text = worker_data.answer_text

    elif request_type == "sale":
        worker_name = "sales_agent"
        worker_result = sales_agent.run_sync(request_text)
        worker_data: SalesResponse = worker_result.data
        answer_text = worker_data.answer_text

    else:
        worker_name = "none"
        answer_text = (
            "I'm not sure if you're asking about inventory, a quote, or placing an order. "
            "Please clarify what you need, including product type and quantity."
        )

    return OrchestratorOutput(
        answer_text=answer_text,
        request_type=request_type,
        worker_name=worker_name,
    )


# ---------- Test harness / evaluation ----------

def run_test_scenarios():
    """
    Run all sample requests through the multi-agent system and log results.

    This evaluation:
    - Processes every row in quote_requests_sample.csv
    - Tracks cash balance and inventory value over time
    - Computes cash balance deltas per request
    - Derives a simple fulfillment status and order_details string
    - Writes a rich test_results.csv file for the rubric
    """
    print("Initializing Database")
    init_database()

    # Load and normalize sample requests
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"],
            format="%m/%d/%y",
            errors="coerce",
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return []

    # Initial financial snapshot
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    initial_report = generate_financial_report(initial_date)
    prev_cash = float(initial_report["cash_balance"])
    prev_inventory = float(initial_report["inventory_value"])

    print(f"Initial Cash Balance: ${prev_cash:.2f}")
    print(f"Initial Inventory Value: ${prev_inventory:.2f}")

    results = []

    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")
        context = f"{row.get('job', 'customer')} organizing {row.get('event', 'event')}"
        base_request_text = row.get("request", "")

        print(f"
=== Request {idx + 1} ===")
        print(f"Context: {context}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance before request: ${prev_cash:.2f}")
        print(f"Inventory Value before request: ${prev_inventory:.2f}")

        # Inject the date so agents can reason consistently
        full_request = f"{base_request_text} (Date of request: {request_date})"

        orchestrator_output = call_multi_agent_system(full_request)
        response_text = orchestrator_output.answer_text

        # Updated financial snapshot as-of the same date
        report = generate_financial_report(request_date)
        current_cash = float(report["cash_balance"])
        current_inventory = float(report["inventory_value"])
        cash_delta = current_cash - prev_cash

        print(f"Response: {response_text}")
        print(f"Updated Cash: ${current_cash:.2f} (Δ {cash_delta:+.2f})")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        # Very simple fulfillment heuristic based on the natural language response
        lower_resp = response_text.lower()
        if any(kw in lower_resp for kw in ["order confirmed", "order placed", "we can fulfill", "your order has been recorded"]):
            fulfillment_status = "fulfilled"
        elif any(kw in lower_resp for kw in ["cannot fulfill", "insufficient stock", "unable to fulfill", "out of stock"]):
            fulfillment_status = "unfulfilled"
        elif orchestrator_output.request_type in ("inventory", "other"):
            fulfillment_status = "not_applicable"
        else:
            fulfillment_status = "unknown"

        # Simple order details summary derived from the CSV context
        order_details = f"size={row.get('need_size', 'n/a')}, event={row.get('event', 'n/a')}"        

        results.append(
            {
                "request_id": int(idx + 1),
                "request_date": request_date,
                "request_type": orchestrator_output.request_type,
                "worker_name": orchestrator_output.worker_name,
                "cash_before": prev_cash,
                "cash_after": current_cash,
                "cash_delta": cash_delta,
                "inventory_value": current_inventory,
                "fulfillment_status": fulfillment_status,
                "order_details": order_details,
                "response": response_text,
            }
        )

        # Update previous cash for the next iteration
        prev_cash = current_cash
        prev_inventory = current_inventory

        # Small pause is fine locally but not required for rubric logic
        time.sleep(1)

    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("
===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results



if __name__ == "__main__":
    run_test_scenarios()
