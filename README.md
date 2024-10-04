## PKO BP Bank Expense Python Parser
Easily convert your CSV summaries from the Polish PKO BP bank into detailed expense graphs with this Python script.

[![screen.png](https://i.postimg.cc/D0qSC1XJ/screen.png)](https://postimg.cc/kRgMG6wq)

### Prerequisites:
* Python
* Pandas
* Matplotlib

To run the application:

    python main.py INPUT_DATA.csv CATEGORIES.json (COLORS.json)

Where:

**INPUT_DATA.csv** - The CSV file downloaded from your PKO BP app.

**CATEGORIES.json** - The JSON file where you can customize your expense categories by editing the keywords

**COLORS.json** - (Optional) A JSON file where you can define custom colors for each category by using the same keywords from the categories file.

The output will be:

**monthly_expenses.pdf** - charts with data

**monthly_expenses_summary.csv** - table with all matched categories with monthly summary

**unmatched_transactions.csv** - list of unmatched transactions. Review them to add more categories to JSON file

### Parsing the data - Categories
**ENG**

The script searches for keywords (case-insensitive), ignoring Polish characters. It checks the description, location, and operation fields to find a matching keyword. If no match is found, the transaction will be categorized as "unqualified" under "NIEZAKWALIFIKOWANE".

**PL**

Skrypt przeszukuje słowa kluczowe (bez rozróżniania wielkości liter), ignorując polskie znaki. Sprawdza pola Opis Transakcji, Lokalizacja oraz Data Operacji w celu znalezienia pasującego słowa kluczowego. Jeśli nie znajdzie dopasowania, transakcja zostanie zakwalifikowana jako "NIEZAKWALIFIKOWANE" (niezakwalifikowane).

### Tips
* The more keywords you provide, the more accurate your results will be.
* Think about where your money is going. For example, if you regularly pay someone for music lessons, you can add their name under the "music" or "entertainment" category.
* Parsing is done top to bottom within the categories.json file, so it's a good idea to put more general keywords at the bottom to ensure they're only matched as a last resort.
