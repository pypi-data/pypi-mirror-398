import pandas as pd
from fabriq.document_loader.document_loader import DocumentLoader

class BankStatementParser:
    def __init__(self):
        self.doc_loader = DocumentLoader(multimodal_option="llm")

    def parse_statement(self, file_path):
        tables = self.doc_loader.load_document(file_path, mode="tables")
        table_df = pd.DataFrame()
        for table in tables:
            if isinstance(table, pd.DataFrame):
                columns_lower = [str(col).lower() for col in table.columns]
                transaction_keywords = [
                    "date",
                    "description",
                    "amount",
                    "balance",
                    "transaction",
                    "debit",
                    "credit",
                    "narration",
                    "particulars",
                    "remarks",
                ]
                if (
                    not table.empty
                    and len(table.columns) > 1
                    and len(table) > 1
                    and any(
                        keyword in " ".join(columns_lower)
                        for keyword in transaction_keywords
                    )
                    and "date" in columns_lower[0]
                    or "date" in columns_lower[1]
                ):
                    table_df = pd.concat([table_df, table], ignore_index=True, axis=0)
                    table_df = table_df.dropna(axis=1, how="all")
                    table_df = table_df.loc[:, ~(table_df == "").all()]
        return table_df

    # def extract_name(self,narration):
    #     match = re.search(r'/([A-Z][A-Z\s]+[A-Z])/', narration)
    #     if match:
    #         return match.group(1).strip()
    #     match = re.search(r'(?:UPI/|IMPS/|Recd:IMPS/|RTGS/|NEFT/)([^/]+)/', narration)
    #     if match:
    #         return match.group(1).strip()
    #     # If no name found, return whole narration
    #     return narration

    # def get_balance_metrics(self, df: pd.DataFrame, debit_col='Debit', credit_col='Credit', balance_col='Balance'):
    #     df[debit_col] = pd.to_numeric(df[debit_col].str.replace(',', ''), errors='coerce')
    #     df[credit_col] = pd.to_numeric(df[credit_col].str.replace(',', ''), errors='coerce')
    #     df[balance_col] = pd.to_numeric(df[balance_col].str.replace(',', ''), errors='coerce')
    #     df[[debit_col, credit_col, balance_col]] = df[[debit_col, credit_col, balance_col]].ffill()

    #     opening_balance = df[balance_col].iloc[0] if not df.empty else None
    #     closing_balance = df[balance_col].iloc[-1] if not df.empty else None

    #     total_withdrawal = df[debit_col].sum()
    #     total_deposit = df[credit_col].sum()

    #     return {
    #         'Opening Balance': opening_balance,
    #         'Closing Balance': closing_balance,
    #         'Total Withdrawal Amount': total_withdrawal,
    #         'Total Deposit Amount': total_deposit,
    #     }

    # def get_metrics_by_name(self, df, narration_col='Description', debit_col='Debit', credit_col='Credit'):
    #     df['Name'] = df[narration_col].apply(self.extract_name)
    #     metrics = df.groupby('Name').apply(
    #         lambda x: pd.Series({
    #             'Total Withdrawal Amount': x[debit_col].sum(),
    #             'Total Deposit Amount': x[credit_col].sum(),
    #             'Transaction Count': len(x)
    #         })
    #     ).reset_index()
    #     return metrics
