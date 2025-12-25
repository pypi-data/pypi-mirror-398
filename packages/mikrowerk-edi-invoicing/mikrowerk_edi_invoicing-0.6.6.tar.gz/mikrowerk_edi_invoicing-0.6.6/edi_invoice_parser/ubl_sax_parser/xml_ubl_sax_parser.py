"""
implementation of an ubl xml parser based on sax
"""
from datetime import datetime
import io
from collections import deque
import xml.sax as sax
from decimal import Decimal

from ..model.trade_document_types import (TradeDocument, TradeParty, TradeCurrency, TradeLine, TradePaymentMeans,
                                          AppliedTradeTax, TradePartyAddress, TradePartyContact, BankAccount)

from ..model import XMLAbstractXRechnungParser


class UblSaxHandler(sax.ContentHandler):
    def __init__(self):
        self.x_rechnung: TradeDocument = TradeDocument()
        self.content = ""
        self.stack = deque()
        self.current_attributes = None
        self.current_trade_party = TradeParty()
        self.current_trade_address: TradePartyAddress = TradePartyAddress()
        self.current_trade_contact: TradePartyContact = TradePartyContact()
        self.current_payment_means: TradePaymentMeans = TradePaymentMeans()
        self.current_payment_means_list: [TradePaymentMeans] = []
        self.current_currency: TradeCurrency | None = None
        self.current_trade_line: TradeLine | None = None
        self.trade_line_list: [TradeLine] = []
        self.current_trade_tax: AppliedTradeTax | None = None
        self.applicable_trade_taxes: [AppliedTradeTax] = []
        self.allowance_line_count = 99900
        self.allowance_line_count_incr = 10

    def startDocument(self):
        print("------------------------------ Start ---------------------------------------------------")
        self.x_rechnung = TradeDocument()
        self.stack = deque()
        self.allowance_line_count = 99900

    def endDocument(self):
        self.x_rechnung.name = (
            f"{XMLAbstractXRechnungParser.TYPE_CODES.get(self.x_rechnung.doc_type_code, 'Unknown doc type ')}"
            f" {self.x_rechnung.doc_id}")
        print("------------------------------- End  --------------------------------------------------")

    def startElementNS(self, name, qname, attrs):
        _ns, _tag_name = name
        self.current_attributes = attrs
        self.stack.append((_tag_name, attrs))
        _path = '/'.join([tag for tag, _attrs in self.stack])
        self.content = ""
        match _tag_name:
            case "Party":
                # init all sub entities, if one is missing, so not taking left over
                self.current_trade_party = TradeParty()
                self.current_trade_address = TradePartyAddress()
                self.current_trade_contact = TradePartyContact()
            case "Delivery":
                self.current_trade_party = TradeParty()
                self.current_trade_address = TradePartyAddress()
                self.current_trade_contact = TradePartyContact()
            case "PostalAddress":
                self.current_trade_address = TradePartyAddress()
            case "DeliveryLocation":
                self.current_trade_address = TradePartyAddress()
            case "Contact":
                self.current_trade_contact = TradePartyContact()
            case "DeliveryParty":
                self.current_trade_contact = TradePartyContact()
            case "PaymentMeans":
                self.current_payment_means = TradePaymentMeans()
                self.current_payment_means.payee_account = BankAccount()
            case "InvoiceLine":
                self.current_trade_line = TradeLine()
                self.current_trade_tax = None
            case "TaxSubtotal":
                self.current_trade_tax = AppliedTradeTax()
            case "ClassifiedTaxCategory":
                self.current_trade_tax = AppliedTradeTax()
            case "AllowanceCharge":
                if _path.endswith('Invoice/AllowanceCharge'):
                    self.current_trade_line = TradeLine()
                    self.current_trade_tax = None

        if _path.endswith('/AllowanceCharge/TaxCategory'):
            self.current_trade_tax = AppliedTradeTax()

        print(f">>>>>>>>>>>>>>> start: {_ns} {_tag_name} >>>>>>>>>>>>>>>>")
        print(_path)
        for k, v in attrs.items():
            print(f"{k}: {v}")

    def endElementNS(self, name, qname):
        _ns, _tag_name = name
        _path = '/'.join([tag for tag, attrs in self.stack])
        _close_name, attrs = self.stack.pop()
        _content = self.content.strip()

        # parse any matching closing tags
        if "/Party" in _path:
            self.handle_party(_path, _tag_name, _content, attrs)
        if "/PaymentMeans" in _path:
            self.handle_payment_means(_path, _tag_name, _content, attrs)
        if "/InvoiceLine" in _path:
            self.handle_invoice_line(_path, _tag_name, _content, attrs)
        if "Invoice/AllowanceCharge" in _path:
            self.handle_allowance_charge(_path, _tag_name, _content, attrs)
        if "/ClassifiedTaxCategory" in _path:
            self.handle_trade_tax(_path, _tag_name, _content, attrs)
        if "/TaxTotal/TaxSubtotal" in _path:
            self.handle_trade_tax(_path, _tag_name, _content, attrs)
        if "/AllowanceCharge/TaxCategory" in _path:
            self.handle_trade_tax(_path, _tag_name, _content, attrs)

        # collect results when closing a main tag
        match _tag_name:
            case "PostalAddress":
                self.current_trade_party.postal_address = self.current_trade_address
            case "Contact":
                self.current_trade_party.trade_contact = self.current_trade_contact
            case "PaymentMeans":
                self.current_payment_means_list.append(self.current_payment_means)
            case "InvoiceLine":
                self.current_trade_line.trade_tax = self.current_trade_tax
                self.trade_line_list.append(self.current_trade_line)

        if _path.endswith("Invoice/TaxTotal/TaxSubtotal"):
            self.applicable_trade_taxes.append(self.current_trade_tax)
        elif _path.endswith('Invoice/AllowanceCharge'):
            if hasattr(self.current_trade_line, "trade_tax"):
                self.current_trade_line.trade_tax = self.current_trade_tax
            self.current_trade_line.line_id = f"{self.allowance_line_count}"
            self.allowance_line_count += self.allowance_line_count_incr
            self.current_trade_line.seller_assigned_id = "AllowanceCharge"
            self.current_trade_line.total_amount_net = (
                    self.current_trade_line.unit_price * self.current_trade_line.quantity)
            self.trade_line_list.append(self.current_trade_line)

        # invoice top level properties
        self.handle_invoice(_path, _tag_name, _content, attrs)

        print(f"content:'{_content}'")
        self.content = ''
        print(_path)
        print(f"<<<<<<<<<<<<<<< end: {_ns} {_tag_name} <<<<<<<<<<<<<<<")

    def characters(self, content):
        if content and len(content) > 0:
            self.content += content

    def handle_invoice(self, path: str, tag, content: str, attrs=None):
        match path:
            case "Invoice/ID":
                self.x_rechnung.doc_id = content
            case "Invoice/IssueDate":
                self.x_rechnung.issued_date_time = datetime.fromisoformat(content)
            case "Invoice/Delivery/ActualDeliveryDate":
                self.x_rechnung.delivered_date_time = datetime.fromisoformat(content)
            case "Invoice/InvoiceTypeCode":
                self.x_rechnung.doc_type_code = content
            case "Invoice/DocumentCurrencyCode":
                self.x_rechnung.currency_code = content
            case "Invoice/BuyerReference":
                self.x_rechnung.buyer_reference = content
            case "Invoice/OrderReference/ID":
                self.x_rechnung.order_reference = content
            case "Invoice/OrderReference/SalesOrderID":
                self.x_rechnung.sales_order_reference = content
            case "Invoice/DespatchDocumentReference/ID":
                self.x_rechnung.dispatch_document_reference = content
            case "Invoice/AccountingSupplierParty":
                self.x_rechnung.seller = self.current_trade_party
            case "Invoice/AccountingCustomerParty":
                self.x_rechnung.buyer = self.current_trade_party
            case "Invoice/PaymentMeans":
                if self.current_payment_means_list and len(self.current_payment_means_list) > 0:
                    self.x_rechnung.payment_means = self.current_payment_means_list[0]
            case "Invoice/PaymentTerms/Note":
                self.x_rechnung.payment_terms = content
            # case "Invoice/AllowanceCharge/Amount":
            #     self.x_rechnung.allowance_total_amount = Decimal(content)
            case "Invoice/TaxTotal/TaxAmount":
                self.x_rechnung.tax_total_amount = [TradeCurrency(float(content),
                                                                  attrs.get('currencyID', 'EUR'))]
            case "Invoice/TaxTotal/TaxSubtotal/TaxableAmount":
                self.x_rechnung.tax_basis_total_amount = TradeCurrency(float(content),
                                                                       attrs.get('currencyID', 'EUR'))
            case "Invoice/LegalMonetaryTotal/TaxInclusiveAmount":
                self.x_rechnung.grand_total_amount = TradeCurrency(float(content),
                                                                   attrs.get('currencyID', 'EUR'))
            case "Invoice/LegalMonetaryTotal/PrepaidAmount":
                self.x_rechnung.total_prepaid_amount = Decimal(content)
            case "Invoice/LegalMonetaryTotal/PayableAmount":
                self.x_rechnung.due_payable_amount = Decimal(content)
            case "Invoice/InvoiceLine":
                self.x_rechnung.trade_line_items = self.trade_line_list
            case "Invoice/TaxTotal":
                self.x_rechnung.applicable_trade_taxes = self.applicable_trade_taxes

    def handle_party(self, path: str, tag: str, content: str, attr=None):
        if "/PostalAddress" in path:
            self.handle_postal_address(path, tag, content)
        elif "/Contact" in path:
            self.handle_contact(path, tag, content)
        elif path.endswith("Party/EndpointID"):
            if attr.get((None, "schemeID"), None) == "EM":
                self.current_trade_party.email = content
        elif path.endswith("Party/PartyName/Name"):
            self.current_trade_party.name = content
        elif path.endswith("/Party/PartyTaxScheme/CompanyID"):
            self.current_trade_party.vat_registration_number = content
        elif path.endswith("/Party/PartyLegalEntity/CompanyID"):
            self.current_trade_party.legal_registration_number = content
        elif path.endswith("/Party/PartyLegalEntity/RegistrationName"):
            self.current_trade_party.name = content
        elif path.endswith("/Party/PartyIdentification/ID"):
            self.current_trade_party.global_id = content
            self.current_trade_party.global_id_schema = attr.get((None, "schemeID"), "")

    def handle_postal_address(self, path: str, tag: str, content: str, attr=None):
        if path.endswith("/Party/PostalAddress/StreetName"):
            self.current_trade_address.address_line_1 = content
        elif path.endswith("/Party/PostalAddress/AdditionalStreetName"):
            self.current_trade_address.address_line_2 = content
        elif path.endswith("/Party/PostalAddress/BuildingNumber"):
            self.current_trade_address.address_line_3 = content
        elif path.endswith("/Party/PostalAddress/CityName"):
            self.current_trade_address.city_name = content
        elif path.endswith("/Party/PostalAddress/PostalZone"):
            self.current_trade_address.post_code = content
        elif path.endswith("/Party/PostalAddress/Country/IdentificationCode"):
            self.current_trade_address.country_id = content

    def handle_contact(self, path: str, tag: str, content: str, attr=None):
        if path.endswith("/Party/Contact/Name"):
            self.current_trade_contact.name = content
        elif path.endswith("/Party/Contact/ElectronicMail"):
            self.current_trade_contact.email = content
        elif path.endswith("/Party/Contact/Telephone"):
            self.current_trade_contact.telephone = content

    def handle_payment_means(self, path: str, tag: str, content: str, attr=None):
        if path.endswith("/PaymentMeans/PaymentMeansCode"):
            self.current_payment_means.type_code = content
        elif path.endswith("/PaymentMeans/PaymentID"):
            self.current_payment_means.id = content
        elif path.endswith("/PaymentMeans/PayeeFinancialAccount/ID"):
            self.current_payment_means.payee_account.iban = content
        elif path.endswith("/PaymentMeans/PayeeFinancialAccount/FinancialInstitutionBranch/ID"):
            self.current_payment_means.payee_account.bic = content

    def handle_invoice_line(self, path: str, tag: str, content: str, attr=None):
        if path.endswith("/InvoiceLine/ID"):
            self.current_trade_line.line_id = content
        elif path.endswith("/InvoiceLine/Note"):
            self.current_trade_line.note = content
        elif path.endswith("/InvoiceLine/InvoicedQuantity"):
            self.current_trade_line.quantity = float(content)
            self.current_trade_line.quantity_unit_code = attr.get((None, 'unitCode'), None) if attr else None
        elif path.endswith("/InvoiceLine/LineExtensionAmount"):
            self.current_trade_line.total_amount_net = float(content)
        elif path.endswith("/InvoiceLine/Item/Description"):
            self.current_trade_line.description = content
        elif path.endswith("/InvoiceLine/Note"):
            self.current_trade_line.description += f", {content}" if len(content) > 0 else content
        elif path.endswith("/InvoiceLine/Item/Name"):
            self.current_trade_line.name = content
        elif path.endswith("/InvoiceLine/Item/SellersItemIdentification/ID"):
            self.current_trade_line.seller_assigned_id = content
        elif path.endswith("/InvoiceLine/Item/BuyersItemIdentification/ID"):
            self.current_trade_line.buyer_assigned_id = content
        elif path.endswith("/InvoiceLine/Item/ItemInstance/LotIdentification/LotNumberID"):
            self.current_trade_line.lot_number_id = content
        elif path.endswith("/InvoiceLine/Item/ItemInstance/LotIdentification/ExpiryDate"):
            self.current_trade_line.expiry_date = datetime.fromisoformat(content)
        elif path.endswith("/InvoiceLine/Price/PriceAmount"):
            self.current_trade_line.unit_price = float(content)

    def handle_allowance_charge(self, path: str, tag: str, content: str, attr=None):
        if path.endswith("/AllowanceCharge/AllowanceChargeReason"):
            self.current_trade_line.name = content
        elif path.endswith("/AllowanceCharge/Amount"):
            self.current_trade_line.unit_price = float(content)
        elif path.endswith("/AllowanceCharge/ChargeIndicator"):
            if content.lower() == "true":
                self.current_trade_line.quantity = 1.0
            else:
                self.current_trade_line.quantity = -1.0

    def handle_trade_tax(self, path: str, tag: str, content: str, attr=None):
        if path.endswith("/ClassifiedTaxCategory/ID") or path.endswith("/TaxCategory/ID"):
            self.current_trade_tax.category_code = content
        elif path.endswith("/ClassifiedTaxCategory/TaxScheme/ID") or path.endswith("/TaxCategory/TaxScheme/ID"):
            self.current_trade_tax.type_code = content
            self.current_trade_tax.name = content
        elif path.endswith("/ClassifiedTaxCategory/Percent") or path.endswith("/TaxCategory/Percent"):
            self.current_trade_tax.applicable_percent = float(content)
        elif path.endswith("/TaxSubtotal/TaxableAmount"):
            self.current_trade_tax.basis_amount = float(content)
        elif path.endswith("/TaxSubtotal/TaxAmount"):
            self.current_trade_tax.calculated_amount = float(content)


class XRechnungUblXMLParser(XMLAbstractXRechnungParser):
    @classmethod
    def parse_and_map_x_rechnung(cls, _xml: bytes) -> TradeDocument:
        # create an XMLReader
        parser = sax.make_parser()
        # turn off namespaces
        parser.setFeature(sax.handler.feature_namespaces, 1)
        # override the default ContextHandler
        handler = UblSaxHandler()
        parser.setContentHandler(handler)
        parser.parse(io.BytesIO(_xml))
        x_rechnung = handler.x_rechnung
        return x_rechnung
