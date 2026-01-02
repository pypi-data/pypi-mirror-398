# sevDesk API Client (Inoffiziell)

Python-Client fuer die sevDesk API, generiert aus der OpenAPI-Spezifikation.

## Wichtig

- **Keine offizielle sevDesk Library**
- Nutzung auf eigene Gefahr
- Bei Problemen mit Markenrechten bitte kontaktieren

## Installation

```bash
pip install sevdesk
```

## Quick Start

```python
from sevdesk import Client

client = Client('your-api-token')

# Kontakt suchen/erstellen
contact = client.contactHelper.find_by_mail('max@example.com')
if not contact:
    contact = client.contactHelper.create(name='Max Mustermann', email='max@example.com')

# Rechnung erstellen
invoice = client.invoiceHelper.new(contact=contact, invoiceNumber='REC-001')
invoice.addPosition('Consulting', quantity=10, price=150.00)
invoice.save(status='100')  # 100=Draft
invoice.render()
```

## Helper (High-Level API)

| Helper | Beschreibung |
|--------|--------------|
| `contactHelper` | Kontakte suchen, erstellen, verwalten |
| `invoiceHelper` | Rechnungen erstellen, finalisieren, stornieren |
| `orderHelper` | Angebote, Auftragsbestaetigungen, Lieferscheine |
| `creditNoteHelper` | Gutschriften verwalten |
| `partHelper` | Artikel/Produkte verwalten |
| `letterHelper` | Briefe erstellen, PDF rendern |
| `bankHelper` | Bankkonten, Transaktionen, Kontostand |
| `voucherHelper` | Belege/Ausgaben verwalten |

### contactHelper

```python
contact = client.contactHelper.find_by_mail('mail@example.com')
contact = client.contactHelper.find_by_customfield('revitoid', '123')
contact = client.contactHelper.create(name='Firma GmbH', email='mail@example.com')
```

### invoiceHelper

```python
invoice = client.invoiceHelper.new(contact=contact, invoiceNumber='REC-001')
invoice.addPosition('Service', quantity=1, price=100.00, taxRate=19.0)
invoice.save(status='100')
invoice.render()
pdf = invoice.getPDF(download=True)
```

### letterHelper

```python
letter = client.letterHelper.new(
    contact=contact,
    header='Betreff',
    text='<p>HTML-Inhalt</p>'
)
letter.save()
letter.render()
pdf = letter.getPDF()
```

### bankHelper

```python
accounts = client.bankHelper.get_accounts()
transactions = client.bankHelper.get_transactions(account_id=123, start_date='2025-01-01')
balance = client.bankHelper.get_balance(account_id=123)
credits = client.bankHelper.get_credits(account_id=123)
debits = client.bankHelper.get_debits(account_id=123)
```

### voucherHelper

```python
vouchers = client.voucherHelper.list(status='open')
expenses = client.voucherHelper.get_expenses()
totals = client.voucherHelper.calculate_totals(vouchers)
positions = client.voucherHelper.get_positions(voucher_id=123)
```

### orderHelper

```python
# Angebot erstellen
order = client.orderHelper.new(contact=contact, orderNumber='AN-001', orderType='AN')
order.addPosition('Beratung', quantity=10, price=150.00)
order.save()
pdf = order.getPDF()

# Angebote auflisten
estimates = client.orderHelper.get_estimates()
confirmations = client.orderHelper.get_confirmations()
```

### partHelper

```python
# Artikel erstellen
part = client.partHelper.create(name='Beratung', partNumber='CONS-01', price=150.00)

# Artikel suchen
part = client.partHelper.find_by_number('CONS-01')
part = client.partHelper.get_or_create(name='Service', partNumber='SRV-01', price=100.00)

# Alle Artikel
parts = client.partHelper.list()
```

### creditNoteHelper

```python
creditnotes = client.creditNoteHelper.list()
open_cn = client.creditNoteHelper.get_open()
pdf = client.creditNoteHelper.get_pdf(creditnote_id=123)
```

## Low-Level API (Controller)

Direkter Zugriff auf alle API-Endpoints:

```python
contacts = client.contact.getContacts()
invoices = client.invoice.getInvoices()
orders = client.order.getOrders()
vouchers = client.voucher.getVouchers()
```

## Samples

| Sample | Beschreibung |
|--------|--------------|
| `01_create_invoice.py` | Rechnung mit Positionen erstellen |
| `02_finalize_invoice.py` | Rechnung finalisieren und PDF |
| `03_invoice_status.py` | Rechnungsstatus aendern |
| `04_cancel_invoice.py` | Rechnung stornieren |
| `05_create_letter.py` | Brief erstellen und PDF |
| `06_bank_transactions.py` | Bankkonten und Umsaetze |
| `07_vouchers_expenses.py` | Belege/Ausgaben verwalten |
| `08_orders_estimates.py` | Angebote erstellen und verwalten |
| `09_parts_articles.py` | Artikel/Produkte verwalten |
| `10_creditnotes.py` | Gutschriften verwalten |

Alle Samples nutzen `.env` fuer den API-Key:

```bash
cp .env.example .env
# SEVDESK_API_KEY in .env eintragen
python samples/01_create_invoice.py
```

## Generator

Models und Controller werden aus der OpenAPI-Spec generiert:

```bash
# OpenAPI-Spec herunterladen
curl -o openapi.yaml https://api.sevdesk.de/openapi.yaml

# Generator ausfuehren
python -m generator
```

Patches fuer OpenAPI-Fehler: `generator/patches.yaml`

## Projektstruktur

```
sevdesk/
  controllers/      # Generierte Controller (Low-Level)
  models/           # Generierte Pydantic Models
  converters/       # Generierte Converter
  helpers/          # High-Level Helper (manuell)
  helpermodels/     # Erweiterte Models (manuell)
  undocumented/     # Nicht-dokumentierte API-Endpoints
    controllers/
    models/
generator/          # Code-Generator
samples/            # Beispiel-Scripte
```

## Lizenz

MIT License
