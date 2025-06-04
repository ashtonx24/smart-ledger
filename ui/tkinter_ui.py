def launch_table_window():
    import tkinter as tk
    from tkinter import ttk
    from utils.db_operations import get_all_transactions

    table_window = tk.Toplevel()  # new window on top of entry window
    table_window.title("Smart Ledger - Transactions Table")

    table_frame = tk.Frame(table_window)
    table_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    tree_scroll = tk.Scrollbar(table_frame)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    tree = ttk.Treeview(
        table_frame,
        columns=('ID', 'Date', 'Item', 'Company', 'Amount', 'Type', 'Notes'),
        show='headings',
        yscrollcommand=tree_scroll.set
    )
    tree_scroll.config(command=tree.yview)

    for col in ('ID', 'Date', 'Item', 'Company', 'Amount', 'Type', 'Notes'):
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    tree.pack(fill=tk.BOTH, expand=True)

    def refresh_table():
        for row in tree.get_children():
            tree.delete(row)
        transactions = get_all_transactions()
        for txn in transactions:
            tree.insert('', tk.END, values=txn)

    refresh_table()

    table_window.mainloop()


def launch_entry_window():
    import tkinter as tk
    from tkinter import ttk
    from utils.db_operations import add_transaction

    class AutocompleteCombobox(ttk.Combobox):
        def set_completion_list(self, completion_list):
            self._completion_list = sorted(completion_list, key=str.lower)
            self['values'] = self._completion_list
            self.bind('<KeyRelease>', self.handle_keyrelease)
            self.position = 0

        def autocomplete(self, delta=0):
            if delta:
                self.position += delta
            else:
                self.position = len(self.get())

            text = self.get().lower()
            if text == '':
                data = self._completion_list
            else:
                data = [item for item in self._completion_list if text in item.lower()]

            if data:
                self['values'] = data
            else:
                self['values'] = self._completion_list

        def handle_keyrelease(self, event):
            if event.keysym == "BackSpace":
                self.autocomplete()
            elif event.keysym == "Left":
                pass
            elif event.keysym == "Right":
                pass
            else:
                self.autocomplete()

    window = tk.Tk()
    window.title("Smart Ledger - Add Transactions")

    # Labels
    tk.Label(window, text="Item Name:").grid(row=0, column=0)
    tk.Label(window, text="Amount:").grid(row=1, column=0)
    tk.Label(window, text="Date (YYYY-MM-DD):").grid(row=2, column=0)
    tk.Label(window, text="Type:").grid(row=3, column=0)
    tk.Label(window, text="Company:").grid(row=4, column=0)
    tk.Label(window, text="Notes:").grid(row=5, column=0)

    item_entry = tk.Entry(window)
    amount_entry = tk.Entry(window)
    date_entry = tk.Entry(window)
    notes_entry = tk.Entry(window)
    item_entry.grid(row=0, column=1)
    amount_entry.grid(row=1, column=1)
    date_entry.grid(row=2, column=1)
    notes_entry.grid(row=5, column=1)

    type_var = tk.StringVar(window)
    type_dropdown = ttk.Combobox(window, textvariable=type_var)
    type_dropdown['values'] = ("Income", "Expense")
    type_dropdown.grid(row=3, column=1)
    type_dropdown.current(0)

    # Company dropdown with autocomplete
    company_list = [
        "Apple", "Microsoft", "Google", "Amazon", "Tesla",
        "Meta", "Netflix", "Coca-Cola", "Pepsi", "Nike",
        "Intel", "AMD", "IBM", "Samsung", "Sony",
        "Oracle", "Salesforce", "Twitter", "Uber", "Airbnb"
    ]
    company_var = tk.StringVar(window)
    company_dropdown = AutocompleteCombobox(window, textvariable=company_var)
    company_dropdown.set_completion_list(company_list)
    company_dropdown.grid(row=4, column=1)

    status_label = tk.Label(window, text="", font=("Arial", 10))
    status_label.grid(row=7, columnspan=2)

    def submit_transaction():
        item = item_entry.get()
        amount = amount_entry.get()
        date = date_entry.get()
        txn_type = type_var.get().lower()
        notes = notes_entry.get()
        company = company_var.get()

        if txn_type == "income":
            txn_type = "credit"
        elif txn_type == "expense":
            txn_type = "debit"
        else:
            status_label.config(text="Invalid transaction type selected", fg="red")
            return

        if item and amount and date and company:
            try:
                transaction_data = {
                    'date': date,
                    'item_name': item,
                    'amount': float(amount),
                    'type': txn_type,
                    'company': company,
                    'notes': notes
                }
                add_transaction(transaction_data)
                status_label.config(text="Transaction added!", fg="green")
                # Clear inputs
                item_entry.delete(0, tk.END)
                amount_entry.delete(0, tk.END)
                date_entry.delete(0, tk.END)
                notes_entry.delete(0, tk.END)
                company_dropdown.set('')
                type_dropdown.current(0)
            except ValueError:
                status_label.config(text="Invalid amount entered", fg="red")
        else:
            status_label.config(text="Please fill all fields", fg="red")

    submit_btn = tk.Button(window, text="Add Transaction", command=submit_transaction)
    submit_btn.grid(row=6, columnspan=2, pady=10)

    # Button to launch the table window
    open_table_btn = tk.Button(window, text="Show Transactions Table", command=launch_table_window)
    open_table_btn.grid(row=8, columnspan=2, pady=10)

    window.mainloop()


if __name__ == "__main__":
    launch_entry_window()