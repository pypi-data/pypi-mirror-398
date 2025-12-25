from dataclasses import dataclass
import datetime

"""
UBL Document Type (XML Root)	Description	UNCL 1001 Code (Example)
"""

ubl_doc_codes = {
    "ApplicationResponse": ('ApplicationResponse', 431, 'Response to an application/message'),
    "Catalogue": ('Catalogue', 71, 'Product catalogue'),
    "CatalogueRequest": ('CatalogueRequest', 171, 'Catalogue request'),
    "CreditNote": ('CreditNote', 381, 'Commercial Credit note'),
    "DebitNote": ('DebitNote', 383, 'Debit note'),
    "DespatchAdvice": ('DespatchAdvice', 250, 'Despatch advice (Advance Ship Notice)'),
    "Invoice": ('Invoice', 380, 'Commercial Invoice'),
    "Order": ('Order', 220, 'Order'),
    "OrderChange": ('OrderChange', 222, 'Order change'),
    "OrderResponse": ('OrderResponse', 255, 'Order response (confirmation/rejection)'),
    "Quotation": ('Quotation', 83, 'Quotation'),
    "RequestForQuotation": ('RequestForQuotation', 135, 'Request for quotation'),
    "RemittanceAdvice": ('RemittanceAdvice', 256, 'Remittance advice'),
    "Statement": ('Statement', 86, 'Account statement / Balance confirmation'),
    "UtilityStatement": ('Utility statement', 490, 'Statement (electricity, gas, etc.)'),
}


@dataclass
class TradePartyAddress:
    post_code: str = None
    city_name: str = None
    country_id: str = None
    country_subdivision_id: str = None
    address_line_1: str = None
    address_line_2: str = None
    address_line_3: str = None


@dataclass
class TradePartyContact:
    name: str = None
    department_name: str = None
    telephone: str = None
    fax: str = None
    email: str = None


@dataclass
class TradeParty:
    name: str= None
    description: str = None  # 'Description'
    global_id: int = 0  # 'Global ID'
    global_id_schema: str = None  # 'Global Schema'
    id: str = None  # 'id'
    address: TradePartyAddress | None = None
    contact: TradePartyContact | None = None
    email: str = None  # 'Email'
    vat_registration_number: str | None = None
    fiscal_registration_number: str | None = None
    legal_registration_number: str | None = None


@dataclass
class AppliedTradeTax:
    name: str = None
    type_code: str = None
    category_code: str = None
    applicable_percent: float = None
    basis_amount: float = None
    calculated_amount: float = None


@dataclass
class TradeLine:
    line_id: int = 0
    article_code: str | None = None
    name: str | None = None
    description: str | None = None
    quantity: float = None
    quantity_unit_code: str = None
    unit_price: float = None
    unit_price_gross: float = None
    tax: AppliedTradeTax | None = None
    total_amount_net: float = None
    total_amount: float = None
    total_allowance_charge: float = None
    global_product_id: str = None  # 'Global Product ID')
    global_product_scheme_id: str = None  # 'Global Product Scheme ID')
    seller_assigned_id: str = None  # 'Seller Assigned ID')
    buyer_assigned_id: str = None  # 'Buyer Assigned ID')


@dataclass
class TradeCurrency:
    amount: float
    currency_code: str

    @staticmethod
    def from_currency_tuple(currency_tuple: tuple) -> 'TradeCurrency':
        return TradeCurrency(*currency_tuple)


@dataclass
class BankAccount:
    iban: str | None = None
    bic: str = None
    name: str = None


@dataclass
class FinancialCard:
    id: str
    cardholder_name: str | None = None


@dataclass
class TradePaymentMeans:
    id: str = None
    type_code: str = None
    information: str = None
    financial_card: FinancialCard = None
    payee_account: BankAccount = None


@dataclass
class TradeDocument:
    """
    Model of a Trade Document
    """
    name: str = None
    doc_type_code: int = 0  # Document Type Code: ubl_doc_codes
    doc_type_name: str = None
    doc_id: str = None
    project: str = None
    issued_date_time: datetime = None  # 'Date'
    delivered_date_time: datetime = None  # 'Delivered Date'
    languages: str = None  # 'Languages'
    notes: str = None  # 'Notes'
    sender_reference: str = None  # 'Buyer Reference'
    receiver_reference: str | None = None
    dispatch_reference: str | None = None
    order_reference: str | None = None
    sender: TradeParty = None
    receiver: TradeParty = None
    payee: TradeParty = None
    invoicee: TradeParty = None
    currency_code: str = None  # 'Currency Code'
    payment_means: TradePaymentMeans = None
    payment_terms: str | None = None  # 'Payment Terms'
    due_date_time: datetime = None
    line_total_amount: float = None  # 'Line Total Amount'
    charge_total_amount: float = None  # 'Charge Total Amount'
    allowance_total_amount: float = None  # 'Allowance Total Amount'
    tax_basis_total_amount: TradeCurrency = None
    tax_total_amount: [TradeCurrency] = None  # 'Tax Grand Total Amount'
    grand_total_amount: TradeCurrency = None  # 'Grand Total Amount'
    total_prepaid_amount: float = None  # 'Total Prepaid Amount'
    due_payable_amount: float = None  # 'Due Payable Amount'
    trade_line_items: [TradeLine] = None
    applicable_trade_taxes: [AppliedTradeTax] = None
