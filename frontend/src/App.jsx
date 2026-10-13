import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [transactions, setTransactions] = useState([]);
  
const BUSINESS_ID = 1;
const API_URL = "http://127.0.0.1:8000";

const [loading, setLoading] = useState(true);
const [apiError, setApiError] = useState("");

useEffect(() => {
  async function loadDashboard() {
    try {
      setApiError("");

      const [transactionsResponse, summaryResponse] = await Promise.all([
        fetch(
          `${API_URL}/api/v1/transactions?business_id=${BUSINESS_ID}`
        ),
        fetch(
          `${API_URL}/api/v1/dashboard/summary?business_id=${BUSINESS_ID}`
        ),
      ]);

      if (!transactionsResponse.ok || !summaryResponse.ok) {
        throw new Error("Backend se data load nahi hua.");
      }

      const transactionsData = await transactionsResponse.json();
      await summaryResponse.json();

      setTransactions(transactionsData);
    } catch (error) {
      setApiError(
        "Dashboard data load nahi hua. Backend aur API connection check karo."
      );
    } finally {
      setLoading(false);
    }
  }

  loadDashboard();
}, []);
  
const [direction, setDirection] = useState("income");
const [amount, setAmount] = useState("");
const [description, setDescription] = useState("");
const [category, setCategory] = useState("Sales");
const [paymentMode, setPaymentMode] = useState("cash");

  const totalIncome = transactions
    .filter((t) => t.direction === "income")
    .reduce((sum, t) => sum + Number(t.amount), 0);

  const totalExpenses = transactions
    .filter((t) => t.direction === "expense")
    .reduce((sum, t) => sum + Number(t.amount), 0);

  const netCashFlow = totalIncome - totalExpenses;

 
async function addTransaction(event) {
  event.preventDefault();
console.log("ADD TRANSACTION FUNCTION CALLED");
  if (!amount || Number(amount) <= 0 || !description.trim()) {
    alert("Please enter a valid amount and description.");
    return;
  }

  const transaction = {
    business_id: 1,
    direction: direction,
    amount: Number(amount),
    category: category || "Other",
    txn_date: new Date().toISOString().slice(0, 10),
    description: description.trim(),
    payment_mode: paymentMode,
  };

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/api/v1/transactions",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(transaction),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        errorData.detail
          ? JSON.stringify(errorData.detail)
          : "Transaction save nahi hua."
      );
    }

    const savedTransaction = await response.json();

    setTransactions((previous) => [
      savedTransaction,
      ...previous,
    ]);

    setAmount("");
    setDescription("");

    alert("Transaction successfully database mein save ho gaya!");
  } catch (error) {
    console.error("Transaction save error:", error);
    alert("Transaction save nahi hua: " + error.message);
  }
}

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>VyapaarSaathi</h2>
        <p className="tagline">Your business, simplified.</p>

        <nav>
          <div className="nav-item active">Dashboard</div>
          <div className="nav-item">Transactions</div>
          <div className="nav-item">Cash Flow</div>
          <div className="nav-item">Credit Readiness</div>
          <div className="nav-item">Government Schemes</div>
        </nav>

        <p className="sidebar-footer">Made for MSME owners</p>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">BUSINESS OVERVIEW</p>
            <h1>Good day, Business Owner!</h1>
            <p className="subtitle">
              Understand your business finances at a glance.
            </p>
          </div>
          <span className="status">● Demo dashboard</span>
        </header>

        <section className="summary-grid">
          <article className="summary-card">
            <p>Total Income</p>
            <h2>₹{totalIncome.toLocaleString("en-IN")}</h2>
            <span>Money received</span>
          </article>

          <article className="summary-card">
            <p>Total Expenses</p>
            <h2>₹{totalExpenses.toLocaleString("en-IN")}</h2>
            <span>Money spent</span>
          </article>

          <article className="summary-card">
            <p>Net Cash Flow</p>
            <h2>₹{netCashFlow.toLocaleString("en-IN")}</h2>
            <span>Income minus expenses</span>
          </article>
        </section>

        <section className="content-grid">
          <article className="panel">
            <h2>Add a transaction</h2>
            <p className="panel-description">
              Record money received or money spent.
            </p>

            <form onSubmit={addTransaction}>
              <label>Transaction type</label>
              <div className="type-switch">
                <button
                  type="button"
                  className={direction === "income" ? "selected income" : ""}
                  onClick={() => setDirection("income")}
                >
                  + Income
                </button>
                <button
                  type="button"
                  className={direction === "expense" ? "selected expense" : ""}
                  onClick={() => setDirection("expense")}
                >
                  − Expense
                </button>
              </div>

              <label htmlFor="amount">Amount (₹)</label>
              <input
                id="amount"
                type="number"
                min="0.01"
                step="0.01"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="e.g. 500"
                required
              />

            
<label htmlFor="description">Description</label>
<input
  id="description"
  value={description}
  onChange={(event) => setDescription(event.target.value)}
  placeholder="e.g. Sold goods to Ramesh"
  required
/>

{/* Category dropdown - yahan add kiya hai */}
<label htmlFor="category">Category</label>
<select
  id="category"
  value={category}
  onChange={(event) => setCategory(event.target.value)}
>
  <option value="Sales">Sales</option>
  <option value="Inventory">Inventory</option>
  <option value="Office Supplies">Office Supplies</option>
  <option value="Transport">Transport</option>
  <option value="Other">Other</option>
</select>

<label htmlFor="paymentMode">Payment mode</label>
<select
  id="paymentMode"
  value={paymentMode}
  onChange={(event) => setPaymentMode(event.target.value)}
>
  <option value="cash">Cash</option>
  <option value="upi">UPI</option>
  <option value="bank">Bank transfer</option>
</select>
              <select
                id="paymentMode"
                value={paymentMode}
                onChange={(event) => setPaymentMode(event.target.value)}
              >
                <option value="cash">Cash</option>
                <option value="upi">UPI</option>
                <option value="bank">Bank transfer</option>
              </select>

              <button className="primary-button" type="submit">
                Save transaction
              </button>
            </form>
          </article>

          <article className="panel">
            <h2>Recent transactions</h2>
            <p className="panel-description">
              Your newly entered transactions appear here.
            </p>

            {transactions.length === 0 ? (
              <div className="empty-state">
                <span className="empty-icon">₹</span>
                <h3>No transactions yet</h3>
                <p>Add your first transaction using the form.</p>
              </div>
            ) : (
              <div className="transaction-list">
                {transactions.map((transaction) => (
                  <div className="transaction-row" key={transaction.id}>
                    <div className="transaction-icon">
                      {transaction.direction === "income" ? "↙" : "↗"}
                    </div>
                    <div className="transaction-details">
                      <strong>{transaction.description}</strong>
                      <span>
                        {transaction.txn_date} · {transaction.payment_mode}
                      </span>
                    </div>
                    <strong
                      className={
                        transaction.direction === "income"
                          ? "income-text"
                          : "expense-text"
                      }
                    >
                      {transaction.direction === "income" ? "+" : "−"}₹
                      {transaction.amount.toLocaleString("en-IN")}
                    </strong>
                  </div>
                ))}
              </div>
            )}
          </article>
        </section>

        <footer>
          VyapaarSaathi · MSME Financial Assistant
        </footer>
      </main>
    </div>
  );
}

export default App;