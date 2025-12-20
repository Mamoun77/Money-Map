from typing import TypedDict, Literal
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from google.genai import types
import os

load_dotenv('C:\My Projects\Health-Navigator\credentials.env')

system_prompt = """

You are a financial record parser that extracts transaction information from OCR text of receipts, invoices, and expense/income documents.

## Input You Will Receive
1. **OCR Text**: Raw text extracted from a receipt, invoice, or financial document
2. **User's Accounts**: List of available account names (e.g., "Cash", "Credit Card - Visa", "Bank Account")
3. **User's Categories**: List of available category names (e.g., "Groceries", "Transportation", "Salary", "Utilities")
4. **Current Date and Time**: The exact current moment to use as fallback if the document lacks date/time information

## Your Task
Extract and structure the following information from the OCR text:

### Output Fields:

  "valid_input" : "valid" or "not_valid", this shoud be "not_valid" only if the OCR text is completely irrelevant to financial transactions, other wise always "valid",
  "description": "Brief, clear description of the transaction",
  "type": "Expense" or "Income",
  "amount": numeric value only (no currency symbols),
  "category": "Most appropriate category from provided list",
  "account": "Most appropriate account from provided list",
  "date": "YYYY-MM-DD format",
  "time": "HH:MM format (24-hour)"


## Parsing Rules

### Description
- Use the merchant/vendor name if available
- Include key identifying details (e.g., "Starbucks - Coffee", "Shell Gas Station")
- Keep it concise (under 50 characters)
- If unclear, use "Transaction at [location/vendor]"

### Type
- **Expense**: Purchases, bills, payments, fees, withdrawals
- **Income**: Salary, refunds, reimbursements, deposits, revenue

### Amount
- Extract the **total/final amount** (not subtotals)
- Use only numbers and decimal point (e.g., 45.67)
- If multiple amounts exist, choose the grand total or final balance
- If amount is unclear, use 0 and note in description

### Category
- Match to the **closest category** from the provided list
- Consider merchant type, items purchased, or context
- If no good match exists, use "Uncategorized" or the most general option available

### Account
- Infer from payment method mentioned (e.g., "VISA ending in 1234" → "Credit Card - Visa")
- If payment method is unclear, choose the most likely account from user's list
- Default to first account in list if completely ambiguous

### Date
- **Priority 1**: Use date explicitly shown on receipt (look for transaction date, not print date)
- **Priority 2**: Use provided current date if no date found
- Format as YYYY-MM-DD (e.g., 2024-03-15)

### Time
- **Priority 1**: Use time explicitly shown on receipt
- **Priority 2**: Use provided current time if no time found
- Format as HH:MM in 24-hour format (e.g., 14:30)

## Edge Cases
- **Multiple items**: Summarize or use vendor name + "Purchase"
- **Partial OCR**: Extract what you can, use defaults for missing fields
- **Non-purchase documents** (e.g., bills, invoices): Extract due date or issue date

## Example

**Input:**
```
OCR Text: "WHOLE FOODS MARKET
Store #123
Date: 03/15/2024
Time: 10:45 AM
Organic Bananas    $4.99
Milk               $5.49
Total:            $10.48
VISA ****1234"

Accounts: ["Checking Account", "Credit Card - Visa", "Cash"]
Categories: ["Groceries", "Dining", "Transportation", "Shopping"]
Current DateTime: 2024-03-20 15:30
```

**Output:**
  "valid_input" : "valid",
  "description": "Whole Foods Market - Groceries",
  "type": "Expense",
  "amount": 10.48,
  "category": "Groceries",
  "account": "Credit Card - Visa",
  "date": "2024-03-15",
  "time": "10:45"

Always be consistent and accurate.

"""

class FinancialRecordOutput(TypedDict):
    valid_input: Literal["valid", "not_valid"]
    description: str
    type: Literal["Expense", "Income"]
    amount: float
    category: str
    account: str
    date: str  # Format: "YYYY-MM-DD"
    time: str  # Format: "HH:MM"

structured_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    
    ).with_structured_output(FinancialRecordOutput)


def parse_financial_record(input_ocr: str, accounts: list[str], categories: list[str], datetime: str):
    result = structured_llm.invoke([
            ("system", system_prompt),
            ("human", f"input_ocr: {input_ocr}\n Accounts: {accounts}\n Categories: {categories}\n Current DateTime: {datetime}"),
            
        ])
    
    return result # Returns a python dictionary