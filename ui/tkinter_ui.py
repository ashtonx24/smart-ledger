import tkinter as tk
from tkinter import ttk
from utils.db_operations import add_transaction, get_all_transactions

def submit_transaction():
    item = item_entry.get()
    amount = amount_entry.get()
    date = date_entry.get()
    txn_type = type_var.get().lower()  # Convert to lowercase to match DB constraint ('credit'/'debit')

    # Map dropdown choices to database values
    if txn_type == "income":
        txn_type = "credit"
    elif txn_type == "expense":
        txn_type = "debit"
    else:
        # fallback or invalid type handling
        status_label.config(text="Invalid transaction type selected", fg="red")
        return

    if item and amount and date:
        try:
            transaction_data = {
                'date': date,
                'item_name': item,
                'amount': float(amount),
                'type': txn_type,        # must be 'credit' or 'debit' per DB schema
                'company': '',           # default empty string for now
                'notes': ''              # optional notes
            }
            add_transaction(transaction_data)
            status_label.config(text="Transaction added!", fg="green")
            # Clear inputs after successful add
            item_entry.delete(0, tk.END)
            amount_entry.delete(0, tk.END)
            date_entry.delete(0, tk.END)
            type_dropdown.current(0)
            refresh_table()
        except ValueError:
            status_label.config(text="Invalid amount entered", fg="red")
    else:
        status_label.config(text="Please fill all fields", fg="red")

def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    transactions = get_all_transactions()
    for txn in transactions:
        tree.insert('', tk.END, values=txn)

def launch_ui():
    window = tk.Tk()
    window.title("Smart Ledger - Add Transactions")

    # Form Labels
    tk.Label(window, text="Item Name:").grid(row=0, column=0)
    tk.Label(window, text="Amount:").grid(row=1, column=0)
    tk.Label(window, text="Date (YYYY-MM-DD):").grid(row=2, column=0)
    tk.Label(window, text="Type:").grid(row=3, column=0)

    global item_entry, amount_entry, date_entry, type_var, status_label, type_dropdown, tree

    # Input Fields
    item_entry = tk.Entry(window)
    amount_entry = tk.Entry(window)
    date_entry = tk.Entry(window)
    item_entry.grid(row=0, column=1)
    amount_entry.grid(row=1, column=1)
    date_entry.grid(row=2, column=1)

    type_var = tk.StringVar(window)
    type_dropdown = ttk.Combobox(window, textvariable=type_var)
    type_dropdown['values'] = ("Income", "Expense")
    type_dropdown.grid(row=3, column=1)
    type_dropdown.current(0)

    # Submit Button
    submit_btn = tk.Button(window, text="Add Transaction", command=submit_transaction)
    submit_btn.grid(row=4, columnspan=2, pady=10)

    # Status Label
    status_label = tk.Label(window, text="", font=("Arial", 10))
    status_label.grid(row=5, columnspan=2)

    # Table Section
    # Scrollbar for the table
    table_frame = tk.Frame(window)
    table_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    tree_scroll = tk.Scrollbar(table_frame)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(table_frame, columns=('ID', 'Date', 'Item', 'Company', 'Amount', 'Type', 'Notes'), 
                        show='headings', yscrollcommand=tree_scroll.set)
    tree_scroll.config(command=tree.yview)

    for col in ('ID', 'Date', 'Item', 'Company', 'Amount', 'Type', 'Notes'):
        tree.heading(col, text=col)
        tree.column(col, anchor="center")
    
    tree.pack(fill=tk.BOTH, expand=True)
    # Initial load of data
    refresh_table()

    window.mainloop()