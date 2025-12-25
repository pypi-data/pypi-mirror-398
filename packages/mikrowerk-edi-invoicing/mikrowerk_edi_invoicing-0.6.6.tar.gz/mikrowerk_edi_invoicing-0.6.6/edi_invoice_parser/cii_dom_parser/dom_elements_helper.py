from .models.elements import (StringElement, DirectDateTimeElement, DateTimeElement, DecimalElement,
                              IndicatorElement, QuantityElement, CurrencyElement, ClassificationElement,
                              Container)
from .models.party import EmailURI, PhoneNumber, FaxNumber
from .models.note import IncludedNote
from .models.payment import PaymentTerms
from .models.container import IDContainer, StringContainer, CurrencyContainer

"""
Code zur Beschreibung des Datumsformats
Codeliste:
102 = CCYYMMDD
201 = YYMMDDHHMM
615 = YYWW
616 = CCYYWW
720 = THHMMTHHMM
804 = Anzahl Tage
Beispiel: <DocumentDate FormatCode="102">20160331</DocumentDate>
"""


def get_value(self) -> any:
    return self._value


def get_float_value(self) -> any:
    return float(self._value) if self._value is not None else None


def get_value_from_amount(self) -> any:
    return float(self._amount) if self._amount is not None else None


def get_currency(self) -> (any, any):
    if self._amount:
        return float(self._amount), self._amount
    else:
        return self._amount, self._amount


def get_currencies(self) -> [(any, any)]:
    res = []
    if self.children:
        for currency in self.children:
            res.append(currency)
    return res


def get_string_from_text(self) -> str:
    return self._text


def get_string_from_payment_terms(self, separator) -> str:
    return str(self.description)


def get_string_from_value(self) -> str:
    return str(self._value)


def get_string_from_data(self) -> str:
    return str(self._data)


def get_string_from_address(self) -> str:
    return str(self.address)


def get_string_from_number(self) -> str:
    return str(self.number)


def get_string_from_date(self) -> str:
    return str(self._value)


def get_string_from_quantity(self) -> str:
    return str(f"{self._amount} {self._unit_code}")


def get_string_from_currency(self) -> str:
    return str(f"{self._amount} {self._currency}")


def get_string_from_content(self, separator) -> str:
    if not self.content:
        return ""
    return self.content.get_string_elements(separator)


def get_string_elements(self, separator: str = ';') -> str:
    res = ""
    _separator = ""
    if self.children:
        for child in self.children:
            if isinstance(child, str):
                res += _separator + child
            elif isinstance(child, tuple):
                p1, p2 = child[:]
                res += f"{p1} {p2} {_separator}"
            else:
                res += _separator + child.get_string(separator)
            _separator = separator
    return res


def get_ids(self) -> list:
    res = list()
    if self.children:
        for text, _id, in self.children:
            res.append({
                'id': _id,
                'schema': text,
            })
    return res


StringElement.get_string = get_string_from_text
StringContainer.get_string = get_string_elements
DirectDateTimeElement.get_string = get_string_from_date
DateTimeElement.get_string = get_string_from_date
DateTimeElement.get_value = get_value
DecimalElement.get_string = get_string_from_value
DecimalElement.get_value = get_float_value
IndicatorElement.get_string = get_string_from_value
QuantityElement.get_string = get_string_from_quantity
QuantityElement.get_value = get_value_from_amount
CurrencyElement.get_currency = get_currency
CurrencyContainer.get_string = get_string_elements
CurrencyContainer.get_currencies = get_currencies
ClassificationElement.get_string = get_string_from_text
IDContainer.get_object = get_ids
EmailURI.get_string = get_string_from_address
PhoneNumber.get_string = get_string_from_number
FaxNumber.get_string = get_string_from_number
Container.get_string_elements = get_string_elements
IncludedNote.get_string = get_string_from_content
IncludedNote.get_string_elements = get_string_elements
PaymentTerms.get_string = get_string_from_payment_terms
