"""
GUI Pages module

Contains all page widgets for the main window.
"""

from .base import BasePage
from .setup import SetupPage
from .connection import ConnectionPage
from .proxy_settings import ProxySettingsPage
from .converters import ConvertersPage
from .converters_v2 import ConvertersPageV2  # New unified converters page
from .location import LocationPage
from .sn_handler import SNHandlerPage
from .software import SoftwarePage
from .about import AboutPage
from .log import LogPage
from .asset import AssetPage
from .rootcause import RootCausePage
from .production import ProductionPage
from .product import ProductPage

__all__ = [
    "BasePage",
    "SetupPage",
    "ConnectionPage",
    "ProxySettingsPage",
    "ConvertersPage",
    "ConvertersPageV2",
    "LocationPage",
    "SNHandlerPage",
    "SoftwarePage",
    "AboutPage",
    "LogPage",
    "AssetPage",
    "RootCausePage",
    "ProductionPage",
    "ProductPage",
]
