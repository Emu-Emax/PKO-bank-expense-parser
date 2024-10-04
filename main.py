import sys
import json
import unidecode
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages

def load_colors(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_categories(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_transactions(csv_file):
    df = pd.read_csv(csv_file, delimiter=",", skiprows=1, encoding='ISO-8859-2')

    df.columns = [
        "Transaction Date", "Value Date", "Transaction Type", "Amount", "Currency",
        "Balance After Transaction", "Description", "Location", "Operation Date and Time",
        "Original Amount", "Card Number", "", ""
    ]

    # cleaning
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%Y-%m-%d')
    df['Amount'] = df['Amount'].astype(str)
    df['Amount'] = df['Amount'].str.replace(",", ".").astype(float)
    df = df[df['Amount'] < 0]

    return df[['Transaction Date', 'Description', 'Amount','Location',"Operation Date and Time"]]


def categorize_transaction(description, location, operation_date_time, categories):
    # Normalize inputs
    normalized_description = unidecode.unidecode(description).lower() if isinstance(description, str) else ""
    normalized_location = unidecode.unidecode(location).lower() if isinstance(location, str) else ""
    normalized_operation = unidecode.unidecode(operation_date_time).lower() if isinstance(operation_date_time, str) else ""

    # Check each top-level category and its keywords
    for broad_category, subcategories in categories.items():
        for subcategory, keywords in subcategories.items():
            for keyword in keywords:
                normalized_keyword = unidecode.unidecode(keyword).lower()
                # Check description, location, and operation date and time
                if normalized_keyword in normalized_description or normalized_keyword in normalized_location or normalized_keyword in normalized_operation:
                    return broad_category, subcategory

    return "NIEZAKWALIFIKOWANE", False  # No match found


def group_transactions_by_month(transactions, categories):
    # Add a Month column to the DataFrame
    transactions['Month'] = transactions['Transaction Date'].dt.to_period('M')

    categorized_data = transactions.apply(
        lambda row: categorize_transaction(row['Description'], row['Location'], row['Operation Date and Time'], categories), axis=1
    )

    # Split the categorized data into two columns: Category and Matched
    transactions['Category'], transactions['Matched'] = zip(*categorized_data)

    # Ensure amounts are positive by taking the absolute value
    transactions['Amount'] = transactions['Amount'].abs()

    # Filter unmatched transactions and save them to a CSV file
    unmatched_transactions = transactions[transactions['Matched'] == False]
    unmatched_transactions.to_csv('unmatched_transactions.csv', index=False)

    # Group by Month and Category, then sum the Amount for each group
    monthly_summary = transactions.groupby(['Month', 'Category'])['Amount'].sum().unstack(fill_value=0)

    # Add a 'Total' column that sums all categories for each month
    monthly_summary['Total'] = monthly_summary.sum(axis=1)

    # Reorder columns to place 'Miscellaneous' just before 'Total'
    if 'Miscellaneous' in monthly_summary.columns:
        # Move 'Miscellaneous' to the end, right before 'Total'
        columns = [col for col in monthly_summary.columns if col != 'Miscellaneous' and col != 'Total']
        columns.append('Miscellaneous')
        columns.append('Total')
        monthly_summary = monthly_summary[columns]

    # Format the summary to show two decimal places
    monthly_summary = monthly_summary.applymap(lambda x: f"{x:.2f}")

    return monthly_summary

def save_all_bar_charts_to_pdf(monthly_summary, colors_map):
    file_name='monthly_expenses.pdf'
    # Open a PDF file to save the charts
    with PdfPages(file_name) as pdf:
        # Loop through each month in the summary and generate a bar chart
        for month in monthly_summary.index:
            # Exclude the 'Total' column from the plot
            month_data = monthly_summary.loc[month].drop('Total').astype(float)
            # Only include categories with non-zero expenses
            month_data = month_data[month_data > 0]

            # Draw the bar chart for each month and save it in the PDF
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

    # Adding the numerical values above each bar
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

    transactions = load_transactions(transactions_file)
    categories = load_categories(categories_file)
    colors_map = load_colors(colors_file) if colors_file else {}

    monthly_summary = group_transactions_by_month(transactions, categories)
    save_all_bar_charts_to_pdf(monthly_summary, colors_map)

    monthly_summary.to_csv('monthly_expenses_summary.csv')

if __name__ == "__main__":
    main()