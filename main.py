import sys
import json
import unidecode
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_prepare_transactions(csv_file):
    df = pd.read_csv(csv_file, delimiter=",", skiprows=1, encoding='ISO-8859-2')

    df.columns = [
        "Transaction Date", "Value Date", "Transaction Type", "Amount", "Currency",
        "Balance After Transaction", "Description", "Location", "Operation Date and Time",
        "Original Amount", "Card Number", "", ""
    ]

    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%Y-%m-%d')
    df['Amount'] = df['Amount'].astype(str)
    df['Amount'] = df['Amount'].str.replace(",", ".").astype(float)
    df = df[df['Amount'] < 0]
    df['Amount'] = df['Amount'].abs()

    return df[['Transaction Date', 'Description', 'Amount','Location',"Operation Date and Time","Balance After Transaction"]]

def create_account_balance_over_time(df, pdf):
    plt.figure(figsize=(10, 6))
    plt.plot(df["Transaction Date"], df["Balance After Transaction"], marker='o', linestyle='-', color='b')
    plt.title("Account Balance Over Time", fontsize=16)
    plt.xlabel("Date and Time", fontsize=12)
    plt.ylabel("Balance After Transaction", fontsize=12)
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    df['Rolling Balance'] = df['Balance After Transaction'].rolling(window=5).mean()
    pdf.savefig()
    plt.close()

def plot_top_transactions(df, amount, pdf):
    top_30_transactions = df.sort_values(by='Amount', ascending=False).head(amount)

    plt.figure(figsize=(10, 6))
    plt.axis('off')  # Turn off axes

    table_data = [['Transaction Date', 'Description', 'Amount']] + top_30_transactions[['Transaction Date', 'Description', 'Amount']].values.tolist()
    table = plt.table(cellText=table_data, colLabels=None, loc='center', cellLoc='center', colWidths=[0.2, 0.5, 0.2])

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.auto_set_column_width(col=list(range(len(table_data[0]))))
    plt.title("Top 30 Transactions by Amount", fontsize=12, y=1.1)

    pdf.savefig()
    plt.close()

def create_weekday_expenses_chart(df, pdf):
    df["Weekday"] = df["Transaction Date"].dt.day_name()
    weekday_sum = df.groupby("Weekday")["Amount"].sum()
    weekday_sum = weekday_sum[["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
    plt.figure(figsize=(10, 6))
    weekday_sum.plot(kind='bar', color='skyblue')
    plt.title("Total Transaction Amount by Weekday", fontsize=16)
    plt.xlabel("Weekday", fontsize=12)
    plt.ylabel("Total Amount", fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("weekday_expenses.png", dpi=300)
    pdf.savefig()
    plt.close()





def categorize_transaction(description, location, operation_date_time, categories):
    normalized_description = unidecode.unidecode(description).lower() if isinstance(description, str) else ""
    normalized_location = unidecode.unidecode(location).lower() if isinstance(location, str) else ""
    normalized_operation = unidecode.unidecode(operation_date_time).lower() if isinstance(operation_date_time, str) else ""

    for broad_category, subcategories in categories.items():
        for subcategory, keywords in subcategories.items():
            for keyword in keywords:
                normalized_keyword = unidecode.unidecode(keyword).lower()
                if normalized_keyword in normalized_description or normalized_keyword in normalized_location or normalized_keyword in normalized_operation:
                    return broad_category, subcategory

    return "UNQUALIFIED", False  # No match found


def group_transactions_by_month(transactions, categories):
    transactions['Month'] = transactions['Transaction Date'].dt.to_period('M')

    categorized_data = transactions.apply(
        lambda row: categorize_transaction(row['Description'], row['Location'], row['Operation Date and Time'], categories), axis=1
    )

    # Split the categorized data into two columns: Category and Matched
    transactions['Category'], transactions['Matched'] = zip(*categorized_data)

    # Filter unmatched transactions and save them to a CSV file
    unmatched_transactions = transactions[transactions['Matched'] == False]
    unmatched_transactions.to_csv('unmatched_transactions.csv', index=False)

    # Group by Month and Category, then sum the Amount for each group
    monthly_summary = transactions.groupby(['Month', 'Category'])['Amount'].sum().unstack(fill_value=0)

    # Add a 'Total' column that sums all categories for each month
    monthly_summary['Total'] = monthly_summary.sum(axis=1)
    #monthly_summary.drop(columns=['UNQUALIFIED'], inplace=True)

    monthly_summary = monthly_summary.applymap(lambda x: f"{x:.2f}")

    return monthly_summary

def create_summary_months(monthly_summary, colors_map, pdf):
    for month in monthly_summary.index:
        month_data = monthly_summary.loc[month].drop('Total').astype(float)

        # Only include categories with non-zero expenses
        month_data = month_data[month_data > 0]
        draw_bar_chart_for_month(month, month_data, pdf, colors_map)



def draw_bar_chart_for_month(month, month_data, pdf, colors_map):
    colors = [colors_map.get(cat, 'orange') for cat in month_data.index]  # Default to 'orange' if not found

    plt.figure(figsize=(10, 6))
    bars = month_data.plot(kind='bar', color=colors)

    plt.title(f'Expenses Distribution for {month}', fontsize=16)
    plt.xlabel('Category', fontsize=12)
    plt.ylabel('Amount (PLN)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    for bar in bars.patches:
        height = bar.get_height()
        plt.annotate(f'{height:.2f}',
                     (bar.get_x() + bar.get_width() / 2, height),
                     ha='center', va='bottom', fontsize=10)

    pdf.savefig()
    plt.close()

def main():
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python main.py INPUT_DATA.csv CATEGORIES.json [COLORS.json]")
        sys.exit(1)

    transactions_file = sys.argv[1]
    categories_file = sys.argv[2]
    colors_file = sys.argv[3] if len(sys.argv) == 4 else None
    transactions = load_prepare_transactions(transactions_file)
    categories = load_json(categories_file)
    colors_map = load_json(colors_file) if colors_file else {}
    monthly_summary = group_transactions_by_month(transactions, categories)
    output_filename='report.pdf'

    with PdfPages(output_filename) as pdf:
        plot_top_transactions(transactions, 30, pdf)
        create_weekday_expenses_chart(transactions, pdf)
        create_account_balance_over_time(transactions, pdf)
        create_summary_months(monthly_summary, colors_map, pdf)

if __name__ == "__main__":
    main()