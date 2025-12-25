"""
BankHelper - High-Level Bankkonto- und Transaktionsverwaltung

Beispiele:
    # Alle Bankkonten auflisten
    accounts = sevdesk.bankHelper.get_accounts()

    # Transaktionen eines Kontos abrufen
    transactions = sevdesk.bankHelper.get_transactions(account_id=12345)

    # Transaktionen nach Zeitraum filtern
    transactions = sevdesk.bankHelper.get_transactions(
        account_id=12345,
        start_date='2025-01-01',
        end_date='2025-12-31'
    )

    # Kontostand zu einem Datum
    balance = sevdesk.bankHelper.get_balance(account_id=12345, date='2025-12-01')
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sevdesk.models.checkaccountresponse import CheckAccountResponse
from sevdesk.models.checkaccounttransactionresponse import CheckAccountTransactionResponse


class BankHelper:
    """Helper-Klasse fuer Bank-Operationen auf hohem Level"""

    def __init__(self, client):
        self.client = client

    def get_accounts(self, active_only: bool = True) -> List[CheckAccountResponse]:
        """
        Ruft alle Bankkonten ab.

        Args:
            active_only: Nur aktive Konten (Status 100) zurueckgeben

        Returns:
            Liste von CheckAccountResponse-Objekten
        """
        try:
            accounts = self.client.checkaccount.getCheckAccounts()
            if not accounts:
                return []
            if active_only:
                accounts = [a for a in accounts if str(a.status) == '100']
            return accounts
        except Exception:
            return []

    def get_account_by_id(self, account_id: int) -> Optional[CheckAccountResponse]:
        """
        Ruft ein Bankkonto per ID ab.

        Args:
            account_id: ID des Bankkontos

        Returns:
            CheckAccountResponse oder None
        """
        try:
            result = self.client.checkaccount.getCheckAccountById(account_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None

    def get_account_by_name(self, name: str) -> Optional[CheckAccountResponse]:
        """
        Sucht ein Bankkonto nach Name.

        Args:
            name: Name des Bankkontos (exakte oder teilweise Uebereinstimmung)

        Returns:
            CheckAccountResponse oder None
        """
        accounts = self.get_accounts(active_only=False)
        name_lower = name.lower()
        for account in accounts:
            if account.name and name_lower in account.name.lower():
                return account
        return None

    def get_account_by_iban(self, iban: str) -> Optional[CheckAccountResponse]:
        """
        Sucht ein Bankkonto nach IBAN.

        Args:
            iban: IBAN des Bankkontos

        Returns:
            CheckAccountResponse oder None
        """
        accounts = self.get_accounts(active_only=False)
        iban_clean = iban.replace(' ', '').upper()
        for account in accounts:
            if account.iban and account.iban.replace(' ', '').upper() == iban_clean:
                return account
        return None

    def get_default_account(self) -> Optional[CheckAccountResponse]:
        """
        Ruft das Standard-Bankkonto ab.

        Returns:
            CheckAccountResponse oder None
        """
        accounts = self.get_accounts(active_only=True)
        for account in accounts:
            if str(account.defaultAccount) == '1':
                return account
        # Fallback: erstes aktives Konto
        if accounts:
            return accounts[0]
        return None

    def get_transactions(
        self,
        account_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        only_credit: Optional[bool] = None,
        only_debit: Optional[bool] = None,
        is_booked: Optional[bool] = None,
        payee_payer_name: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> List[CheckAccountTransactionResponse]:
        """
        Ruft Transaktionen ab.

        Args:
            account_id: Bankkonto-ID (optional, alle wenn nicht angegeben)
            start_date: Startdatum (YYYY-MM-DD)
            end_date: Enddatum (YYYY-MM-DD)
            only_credit: Nur Gutschriften (Eingaenge)
            only_debit: Nur Belastungen (Ausgaenge)
            is_booked: Nur gebuchte Transaktionen
            payee_payer_name: Filter nach Empfaenger/Zahler
            purpose: Filter nach Verwendungszweck

        Returns:
            Liste von CheckAccountTransactionResponse-Objekten
        """
        try:
            transactions = self.client.checkaccounttransaction.getTransactions(
                checkAccount_id=account_id,
                checkAccount_objectName="CheckAccount" if account_id else None,
                startDate=start_date,
                endDate=end_date,
                onlyCredit=only_credit,
                onlyDebit=only_debit,
                isBooked=is_booked,
                payeePayerName=payee_payer_name,
                paymtPurpose=purpose
            )
            return transactions if transactions else []
        except Exception:
            return []

    def get_transaction_by_id(self, transaction_id: int) -> Optional[CheckAccountTransactionResponse]:
        """
        Ruft eine Transaktion per ID ab.

        Args:
            transaction_id: ID der Transaktion

        Returns:
            CheckAccountTransactionResponse oder None
        """
        try:
            result = self.client.checkaccounttransaction.getCheckAccountTransactionById(transaction_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None

    def get_balance(self, account_id: int, date: Optional[str] = None) -> Optional[float]:
        """
        Ruft den Kontostand zu einem bestimmten Datum ab.

        Args:
            account_id: Bankkonto-ID
            date: Datum (YYYY-MM-DD), default: heute

        Returns:
            Kontostand als float oder None
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        try:
            result = self.client.checkaccount.getBalanceAtDate(
                checkAccountId=account_id,
                date=date
            )
            if isinstance(result, dict):
                # Response ist z.B. {"objects": "1234.56"}
                balance_str = result.get('objects') or result.get('balance')
                if balance_str:
                    return float(balance_str)
            elif isinstance(result, (int, float, str)):
                return float(result)
            return None
        except Exception:
            return None

    def get_credits(
        self,
        account_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CheckAccountTransactionResponse]:
        """
        Ruft nur Gutschriften (Eingaenge) ab.

        Args:
            account_id: Bankkonto-ID (optional)
            start_date: Startdatum (YYYY-MM-DD)
            end_date: Enddatum (YYYY-MM-DD)

        Returns:
            Liste von Gutschriften
        """
        return self.get_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            only_credit=True
        )

    def get_debits(
        self,
        account_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CheckAccountTransactionResponse]:
        """
        Ruft nur Belastungen (Ausgaenge) ab.

        Args:
            account_id: Bankkonto-ID (optional)
            start_date: Startdatum (YYYY-MM-DD)
            end_date: Enddatum (YYYY-MM-DD)

        Returns:
            Liste von Belastungen
        """
        return self.get_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            only_debit=True
        )

    def get_recent_transactions(
        self,
        account_id: Optional[int] = None,
        days: int = 30
    ) -> List[CheckAccountTransactionResponse]:
        """
        Ruft Transaktionen der letzten X Tage ab.

        Args:
            account_id: Bankkonto-ID (optional)
            days: Anzahl Tage (default: 30)

        Returns:
            Liste von Transaktionen
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self.get_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )

    def sum_transactions(
        self,
        transactions: List[CheckAccountTransactionResponse]
    ) -> dict:
        """
        Berechnet Summen fuer eine Liste von Transaktionen.

        Args:
            transactions: Liste von Transaktionen

        Returns:
            Dict mit 'credits', 'debits', 'total'
        """
        credits = 0.0
        debits = 0.0
        for t in transactions:
            if t.amount:
                amount = float(t.amount)
                if amount >= 0:
                    credits += amount
                else:
                    debits += amount
        return {
            'credits': credits,
            'debits': debits,
            'total': credits + debits
        }
