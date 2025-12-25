"""
This implements a mapper from a drafthorse parsed x-rechnung-xml to the internal XRechnung object
"""
import logging
from lxml import etree

from .model.trade_document_types import TradeDocument
from .cii_dom_parser import XRechnungCIIXMLParser
from .ubl_sax_parser.xml_ubl_sax_parser import XRechnungUblXMLParser
from .model.xml_abstract_x_rechnung_parser import XMLAbstractXRechnungParser

_logger = logging.getLogger(__name__)


def parse_and_map_x_rechnung(_xml: bytes) -> TradeDocument:
    """

    Args:
        _xml: bytes with xml file

    Returns: XRechnung

    """
    _parser = get_xml_parser_for_doc_type(_xml)
    if _parser is None:
        raise ValueError('xml format not supported for any parser"')
    return _parser.parse_and_map_x_rechnung(_xml)


def get_xml_parser_for_doc_type(_xml: bytes) -> XMLAbstractXRechnungParser:
    _parser = None
    tree = etree.fromstring(_xml)
    if tree.tag == '{urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100}CrossIndustryInvoice':
        _parser = XRechnungCIIXMLParser()
    elif tree.tag == '{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice':
        _parser = XRechnungUblXMLParser()
    else:
        _logger.warning(f'No parser found, unsupported XML tag: {tree.tag}')
    return _parser


def check_if_parser_is_available(_xml: bytes) -> bool:
    return get_xml_parser_for_doc_type(_xml) is not None

