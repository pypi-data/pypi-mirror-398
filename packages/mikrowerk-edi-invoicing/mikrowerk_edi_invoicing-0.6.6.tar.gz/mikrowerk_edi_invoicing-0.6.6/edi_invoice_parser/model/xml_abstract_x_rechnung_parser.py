from abc import ABC, abstractmethod

from ..model.trade_document_types import TradeDocument


class XMLAbstractXRechnungParser(ABC):
    TYPE_CODES = {
        '326': 'Partial invoice',
        '380': 'Commercial invoice',  # Rechnung
        '384': 'Corrected invoice',  # Rechnungskorrektur
        '389': 'Self-billed invoice',  # Selbst erstelle Rechnung
        '381': 'Credit note',  # Gutschrift
        '875': 'Partial Invoice',  # Abschlagsrechnung
        '876': 'Partial final invoice',  # Teilschlussrechnung
        '877': 'Final invoice'  # Schlussrechnung
    }

    @staticmethod
    @abstractmethod
    def parse_and_map_x_rechnung(_xml: any) -> TradeDocument:
        pass
