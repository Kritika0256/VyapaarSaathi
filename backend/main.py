import os
import re
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="VyapaarSaathi API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
engine = (
    create_engine(DATABASE_URL, pool_pre_ping=True)
    if DATABASE_URL
    else None
)


@app.get("/")
def home():
    return {"message": "VyapaarSaathi backend is running!"}


@app.get("/health")
def health():
    if engine is None:
        raise HTTPException(
            status_code=500,
            detail="DATABASE_URL is missing in .env",
        )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Check server logs.",
        )
    
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    business_id: int = Field(gt=0)
    direction: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str | None = None
    txn_date: date = Field(default_factory=date.today)
    description: str | None = None
    payment_mode: str | None = None


@app.post("/api/v1/transactions")
def create_transaction(transaction: TransactionCreate):
    if engine is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    query = text("""
        INSERT INTO transactions
            (business_id, direction, amount, category,
             txn_date, description, payment_mode)
        VALUES
            (:business_id, :direction, :amount, :category,
             :txn_date, :description, :payment_mode)
        RETURNING id, business_id, direction, amount,
                  category, txn_date, description, payment_mode
    """)

    try:
        with engine.begin() as connection:
            result = connection.execute(
                query,
                transaction.model_dump()
            )
            row = result.mappings().one()

        return dict(row)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=400,
            detail="Could not save transaction. Check business_id and database."
        )


@app.get("/api/v1/transactions")
def list_transactions(business_id: int):
    if engine is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT id, business_id, direction, amount,
                           category, txn_date, description, payment_mode
                    FROM transactions
                    WHERE business_id = :business_id
                    ORDER BY txn_date DESC, id DESC
                """),
                {"business_id": business_id}
            )

            return [dict(row) for row in result.mappings().all()]

    except SQLAlchemyError:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve transactions."
        )
@app.post("/api/v1/test-business")
def create_test_business():
    if engine is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        with engine.begin() as connection:
            user_result = connection.execute(
                text("""
                    INSERT INTO users (full_name, email, password_hash)
                    VALUES (:name, :email, :password_hash)
                    ON CONFLICT (email) DO NOTHING
                    RETURNING id
                """),
                {
                    "name": "Test Owner",
                    "email": "test-owner@local.test",
                    "password_hash": "NOT_FOR_LOGIN",
                },
            ).scalar_one_or_none()

            if user_result is None:
                user_result = connection.execute(
                    text("SELECT id FROM users WHERE email = :email"),
                    {"email": "test-owner@local.test"},
                ).scalar_one()

            business_id = connection.execute(
                text("""
                    INSERT INTO businesses (owner_id, business_name, business_type, state)
                    VALUES (:owner_id, :name, :type, :state)
                    RETURNING id
                """),
                {
                    "owner_id": user_result,
                    "name": "Demo Kirana Store",
                    "type": "Retail",
                    "state": "Haryana",
                },
            ).scalar_one()

        return {
            "message": "Test business created",
            "business_id": business_id,
        }

    except SQLAlchemyError:
        raise HTTPException(status_code=400, detail="Could not create test business")
@app.get("/api/v1/dashboard/summary")
def dashboard_summary(business_id: int):
    if engine is None:
        raise HTTPException(
            status_code=500,
            detail="Database not configured",
        )

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        COALESCE(
                            SUM(amount) FILTER (
                                WHERE direction = 'income'
                            ), 0
                        ) AS total_income,
                        COALESCE(
                            SUM(amount) FILTER (
                                WHERE direction = 'expense'
                            ), 0
                        ) AS total_expenses
                    FROM transactions
                    WHERE business_id = :business_id
                """),
                {"business_id": business_id},
            ).mappings().one()

        income = result["total_income"]
        expenses = result["total_expenses"]

        return {
            "business_id": business_id,
            "total_income": income,
            "total_expenses": expenses,
            "net_cash_flow": income - expenses,
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=400,
            detail="Could not calculate dashboard summary.",
        )
    
class NLPExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)



@app.post("/api/v1/nlp/extract")
def extract_transaction(request: NLPExtractRequest):
    original_text = request.text.strip()
    sentence = original_text.lower()

    if not sentence:
        raise HTTPException(
            status_code=422,
            detail="Please provide a transaction sentence.",
        )

    # 1. Extract amount: 200, 200.50 or 1,200
    amount_match = re.search(
        r"(?<!\d)(\d[\d,]*(?:\.\d{1,2})?)(?!\d)",
        sentence,
    )

    amount = None
    if amount_match:
        try:
            amount = float(amount_match.group(1).replace(",", ""))
            if amount <= 0:
                amount = None
        except ValueError:
            amount = None

    # 2. Identify income and expense using basic word rules
    expense_words = [
        "khareeda", "kharida", "khareedi", "kharidi",
        "kharche", "kharch", "paid", "payment",
        "expense", "spent", "bought", "purchase",
        "purchased", "bill diya", "diye",
    ]

    income_words = [
        "becha", "bechi", "sale", "sold", "income",
        "received", "kamaya", "mila", "milay",
        "payment received", "paise aaye",
    ]

    is_expense = any(word in sentence for word in expense_words)
    is_income = any(word in sentence for word in income_words)

    if is_expense and not is_income:
        direction = "expense"
    elif is_income and not is_expense:
        direction = "income"
    else:
        direction = None

    # 3. Identify payment mode
    payment_mode = None

    if re.search(r"\b(cash|nakad)\b", sentence):
        payment_mode = "cash"
    elif re.search(r"\b(upi|gpay|phonepe|paytm)\b", sentence):
        payment_mode = "upi"
    elif re.search(r"\b(bank|neft|imps|rtgs)\b", sentence):
        payment_mode = "bank"

    # 4. Identify simple date phrases
    txn_date = None

    if re.search(r"\b(aaj|today)\b", sentence):
        from datetime import date
        txn_date = date.today().isoformat()

    # 5. Record information that still needs clarification
    missing_fields = []

    if amount is None:
        missing_fields.append("amount")

    if direction is None:
        missing_fields.append("direction")

    return {
        "direction": direction,
        "amount": amount,
        "date": txn_date,
        "description": original_text,
        "payment_mode": payment_mode,
        "needs_confirmation": True,
        "missing_fields": missing_fields,
    }
class NLPConfirmRequest(BaseModel):
    business_id: int = Field(gt=0)
    direction: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    txn_date: date
    description: str = Field(min_length=1, max_length=1000)
    category: str | None = None
    payment_mode: str | None = None
    confirmed: bool
    
@app.post("/api/v1/nlp/confirm")
def confirm_nlp_transaction(request: NLPConfirmRequest):
    if not request.confirmed:
        return {
            "message": "Transaction cancelled. Nothing was saved.",
            "saved": False
        }

    transaction = TransactionCreate(
        business_id=request.business_id,
        direction=request.direction,
        amount=request.amount,
        txn_date=request.txn_date,
        description=request.description,
        category=request.category,
        payment_mode=request.payment_mode,
    )

    saved_transaction = create_transaction(transaction)

    return {
        "message": "Confirmed transaction saved successfully.",
        "saved": True,
        "transaction": saved_transaction,
    }