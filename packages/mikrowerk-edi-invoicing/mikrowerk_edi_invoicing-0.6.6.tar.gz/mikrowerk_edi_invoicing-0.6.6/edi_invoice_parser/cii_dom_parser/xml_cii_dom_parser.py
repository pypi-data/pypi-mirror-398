"""
This implements a mapper from a drafthorse parsed x-rechnung-xml to the internal XRechnung object
"""
from datetime import datetime

from .models.document import Document
from ..model.trade_document_types import (TradeDocument, TradeParty, TradeCurrency, TradeLine, TradePaymentMeans,
                                          AppliedTradeTax, TradePartyAddress, TradePartyContact, BankAccount,
                                          FinancialCard)
from ..model.xml_abstract_x_rechnung_parser import XMLAbstractXRechnungParser


class XRechnungCIIXMLParser(XMLAbstractXRechnungParser):

    @classmethod
    def parse_and_map_x_rechnung(cls, _xml: any) -> TradeDocument:
        doc = Document.parse(_xml)
        return cls().map_to_x_rechnung(doc)

    @classmethod
    def map_to_x_rechnung(cls, doc: any) -> TradeDocument:
        """
        :param doc: Element, the parsed dom root element
        :return:
        """

        return TradeDocument(
            name=f"{cls().TYPE_CODES.get(doc.header.type_code.get_string(), 'Unknown doc type ')} {doc.header.id.get_string()}",
            doc_type_name=f"{cls().TYPE_CODES.get(doc.header.type_code.get_string(), 'Unknown doc type ')}",
            doc_id=doc.header.id.get_string(),
            doc_type_code=int(doc.header.type_code.get_string()) if doc.header.type_code else None,
            issued_date_time=doc.header.issue_date_time.get_value(),
            notes=doc.header.notes.get_string_elements("\n"),
            languages=doc.header.languages.get_string_elements(";"),
            receiver_reference=doc.trade.agreement.buyer_reference.get_string(),
            order_reference=doc.trade.agreement.buyer_order.issuer_assigned_id.get_string(),
            currency_code=doc.trade.settlement.currency_code.get_string(),
            line_total_amount=doc.trade.settlement.monetary_summation.line_total.get_value(),
            charge_total_amount=doc.trade.settlement.monetary_summation.charge_total.get_value(),
            allowance_total_amount=doc.trade.settlement.monetary_summation.allowance_total.get_value(),
            tax_basis_total_amount=TradeCurrency.from_currency_tuple(
                doc.trade.settlement.monetary_summation.tax_basis_total.get_currency()),
            tax_total_amount=[TradeCurrency.from_currency_tuple(tpl) for tpl in
                              doc.trade.settlement.monetary_summation.tax_total_other_currency.get_currencies()],
            # list of currency
            grand_total_amount=TradeCurrency.from_currency_tuple(
                doc.trade.settlement.monetary_summation.grand_total.get_currency()),
            total_prepaid_amount=doc.trade.settlement.monetary_summation.prepaid_total.get_value(),
            due_payable_amount=doc.trade.settlement.monetary_summation.due_amount.get_value(),
            delivered_date_time=datetime.now(),
            payment_means=cls().map_payment_means(
                doc.trade.settlement.payment_means) if doc.trade.settlement.payment_means else None,
            payment_terms=doc.trade.settlement.terms.get_string_elements("\n"),
            sender=cls().map_trade_party(doc.trade.agreement.seller) if hasattr(doc.trade.agreement,
                                                                                "seller") else None,
            invoicee=cls().map_trade_party(doc.trade.agreement.invoicee) if hasattr(doc.trade.agreement,
                                                                                    "invoicee") else None,
            receiver=cls().map_trade_party(doc.trade.agreement.buyer) if hasattr(doc.trade.agreement,
                                                                                 "buyer") else None,
            payee=cls().map_trade_party(doc.trade.agreement.payee) if hasattr(doc.trade.agreement, "payee") else None,
            trade_line_items=cls().map_trade_line_items(doc.trade.items) if hasattr(doc.trade, "items") else None,
            applicable_trade_taxes=cls().map_trade_taxes(doc.trade.settlement.trade_tax) if hasattr(
                doc.trade.settlement,
                "trade_tax") else None
        )

    @classmethod
    def map_trade_party(cls, trade_party: any) -> TradeParty:
        _global_id_schema, _global_id = cls().map_first_id(trade_party.global_id)
        return TradeParty(
            name=trade_party.name.get_string(),
            description=trade_party.description.get_string(),
            global_id=_global_id,
            global_id_schema=_global_id_schema,
            email=cls().map_electronic_address(trade_party.electronic_address, 'EM') if hasattr(trade_party,
                                                                                                "electronic_address") else None,
            vat_registration_number=cls().map_tax_registration(trade_party.tax_registrations, 'VA') if hasattr(
                trade_party, 'tax_registrations') else None,
            fiscal_registration_number=cls().map_tax_registration(trade_party.tax_registrations, 'FC') if hasattr(
                trade_party, 'tax_registrations') else None,
            address=cls().map_trade_address(trade_party.address) if hasattr(trade_party, 'address') else None,
            contact=cls().map_trade_contact(trade_party.contact) if hasattr(trade_party, 'contact') else None,
            id=trade_party.id.get_string() if hasattr(trade_party, 'id') else None,
        )

    @staticmethod
    def map_first_id(global_id: any) -> (str, str):
        if global_id is not None and hasattr(global_id, "children") and len(global_id.children) > 0:
            for child in global_id.children:
                return child
        else:
            return None, None

    @staticmethod
    def map_electronic_address(electronic_address: any, schema_id: str) -> str | None:
        if electronic_address is not None and hasattr(electronic_address, "children") and len(
                electronic_address.children) > 0:
            for child in electronic_address.children:
                if child.uri_ID._scheme_id == schema_id:
                    return child.uri_ID._text

        return None

    @staticmethod
    def map_tax_registration(tax_reg: any, schema_id: str) -> str | None:
        if tax_reg is not None and hasattr(tax_reg, "children") and len(
                tax_reg.children) > 0:
            for child in tax_reg.children:
                if child.id._scheme_id == schema_id and child.id._text:
                    return "".join(child.id._text.split())

        return None

    @staticmethod
    def map_trade_address(trade_address: any) -> TradePartyAddress:
        return TradePartyAddress(
            city_name=trade_address.city_name.get_string(),
            country_id=trade_address.country_id.get_string(),
            country_subdivision_id=trade_address.country_subdivision.get_string(),
            address_line_1=trade_address.line_one.get_string(),
            address_line_2=trade_address.line_two.get_string(),
            address_line_3=trade_address.line_three.get_string(),
            post_code=trade_address.postcode.get_string(),
        )

    @staticmethod
    def map_trade_contact(trade_contact: any) -> TradePartyContact:
        return TradePartyContact(
            name=trade_contact.person_name.get_string(),
            email=trade_contact.email.get_string(),
            telephone=trade_contact.telephone.get_string(),
            department_name=trade_contact.department_name.get_string(),
            fax=trade_contact.fax.get_string(),
        )

    @staticmethod
    def map_bank_account(payment_means: any) -> BankAccount:
        return BankAccount(
            iban="".join(payment_means.payee_account.iban.get_string().split()) if (hasattr(payment_means,
                                                                                            'payee_account')
                                                                                    and payment_means.payee_account.iban.get_string()) else None,
            bic=payment_means.payee_institution.bic.get_string() if (hasattr(payment_means,
                                                                             'payee_institution')
                                                                     and payment_means.payee_institution.bic) else None,
        )

    @staticmethod
    def map_financial_card(financial_card: any) -> FinancialCard:
        return FinancialCard(
            id=financial_card.id.get_string(),
            cardholder_name=financial_card.cardholder_name.get_string(),
        )

    @classmethod
    def map_payment_means(cls, payment_means: any) -> TradePaymentMeans:
        return TradePaymentMeans(
            information=payment_means.information.get_string(),
            type_code=payment_means.type_code.get_string(),
            payee_account=cls().map_bank_account(payment_means) if hasattr(payment_means, 'payee_account') else None,
            financial_card=cls().map_financial_card(payment_means.financial_card) if hasattr(payment_means,
                                                                                             'financial_card') else None,
        )

    @staticmethod
    def map_trade_tax(trade_tax: any) -> AppliedTradeTax:
        return AppliedTradeTax(
            type_code=trade_tax.type_code.get_string(),
            name=f"{trade_tax.type_code.get_string()} {trade_tax.rate_applicable_percent.get_value()}",
            category_code=trade_tax.category_code.get_string(),
            basis_amount=trade_tax.basis_amount.get_value(),
            calculated_amount=trade_tax.calculated_amount.get_value(),
            applicable_percent=trade_tax.rate_applicable_percent.get_value()
        )

    @classmethod
    def map_trade_taxes(cls, trade_taxes: any) -> [TradeLine]:
        res = []
        for child in trade_taxes.children:
            res.append(cls().map_trade_tax(child))
        return res

    @classmethod
    def map_trade_line(cls, trade_line: any) -> TradeLine:
        return TradeLine(
            name=trade_line.product.name.get_string(),
            description=trade_line.product.description.get_string(),
            line_id=trade_line.document.line_id.get_string(),
            unit_price=trade_line.agreement.net.amount.get_value(),
            unit_price_gross=trade_line.agreement.gross.amount.get_value(),
            quantity=trade_line.delivery.billed_quantity.get_value(),
            global_product_id=trade_line.product.global_id.get_string(),
            total_amount_net=trade_line.settlement.monetary_summation.total_amount.get_value(),
            total_allowance_charge=trade_line.settlement.monetary_summation.total_allowance_charge.get_value(),
            quantity_unit_code=trade_line.delivery.billed_quantity._unit_code,
            seller_assigned_id=trade_line.product.seller_assigned_id.get_string(),
            buyer_assigned_id=trade_line.product.buyer_assigned_id.get_string(),
            global_product_scheme_id=trade_line.product.global_id._scheme_id,
            tax=cls().map_trade_tax(trade_line.settlement.trade_tax)
        )

    @classmethod
    def map_trade_line_items(cls, trade_line_items: any) -> [TradeLine]:
        res = []
        for child in trade_line_items.children:
            res.append(cls().map_trade_line(child))
        return res
