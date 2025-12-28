"""
Index configurations for NSE India.

This module defines all available NSE indices organized by categories:
- Broad Market Indices (NIFTY 50, NIFTY Next 50, etc.)
- Sectoral Indices (NIFTY Bank, NIFTY IT, etc.)
- Thematic Indices
- Strategy Indices

Each configuration includes:
- List of available indices
- CSV URLs for constituent stock lists
- Factsheet URLs for detailed information
"""

from __future__ import annotations


class NiftyBroadMarketIndices:
    """Broad Market Indices configuration."""

    indices_list = [
        "Nifty 50",
        "Nifty Next 50",
        "Nifty 100",
        "Nifty 200",
        "Nifty 500",
        "Nifty Midcap 50",
        "Nifty Midcap 100",
        "Nifty Midcap 150",
        "Nifty Smallcap 50",
        "Nifty Smallcap 100",
        "Nifty Smallcap 250",
        "Nifty Midsmallcap 400",
        "Nifty LargeMidcap 250",
    ]

    index_constituent_list_urls = {
        "Nifty 50": "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
        "Nifty Next 50": "https://nsearchives.nseindia.com/content/indices/ind_niftynext50list.csv",
        "Nifty 100": "https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv",
        "Nifty 200": "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv",
        "Nifty 500": "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
        "Nifty Midcap 50": "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap50list.csv",
        "Nifty Midcap 100": "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
        "Nifty Midcap 150": "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
        "Nifty Smallcap 50": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
        "Nifty Smallcap 100": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
        "Nifty Smallcap 250": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
        "Nifty Midsmallcap 400": "https://nsearchives.nseindia.com/content/indices/ind_niftymidsmallcap400list.csv",
        "Nifty LargeMidcap 250": "https://nsearchives.nseindia.com/content/indices/ind_niftylargemidcap250list.csv",
    }

    index_factsheet_urls = {
        "Nifty 50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.pdf",
        "Nifty Next 50": "https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.pdf",
        "Nifty 100": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.pdf",
        "Nifty 200": "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.pdf",
        "Nifty 500": "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.pdf",
        "Nifty Midcap 50": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap50list.pdf",
        "Nifty Midcap 100": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap100list.pdf",
        "Nifty Midcap 150": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.pdf",
        "Nifty Smallcap 50": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap50list.pdf",
        "Nifty Smallcap 100": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap100list.pdf",
        "Nifty Smallcap 250": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.pdf",
        "Nifty Midsmallcap 400": "https://www.niftyindices.com/IndexConstituent/ind_niftymidsmallcap400list.pdf",
        "Nifty LargeMidcap 250": "https://www.niftyindices.com/IndexConstituent/ind_niftylargemidcap250list.pdf",
    }


class NiftySectoralIndices:
    """Sectoral Indices configuration."""

    indices_list = [
        "Nifty Auto",
        "Nifty Bank",
        "Nifty Financial Services",
        "Nifty FMCG",
        "Nifty IT",
        "Nifty Media",
        "Nifty Metal",
        "Nifty Pharma",
        "Nifty PSU Bank",
        "Nifty Private Bank",
        "Nifty Realty",
        "Nifty Healthcare Index",
        "Nifty Consumer Durables",
        "Nifty Oil & Gas",
    ]

    index_constituent_list_urls = {
        "Nifty Auto": "https://nsearchives.nseindia.com/content/indices/ind_niftyautolist.csv",
        "Nifty Bank": "https://nsearchives.nseindia.com/content/indices/ind_niftybanklist.csv",
        "Nifty Financial Services": "https://nsearchives.nseindia.com/content/indices/ind_niftyfinancelist.csv",
        "Nifty FMCG": "https://nsearchives.nseindia.com/content/indices/ind_niftyfmcglist.csv",
        "Nifty IT": "https://nsearchives.nseindia.com/content/indices/ind_niftyitlist.csv",
        "Nifty Media": "https://nsearchives.nseindia.com/content/indices/ind_niftymedialist.csv",
        "Nifty Metal": "https://nsearchives.nseindia.com/content/indices/ind_niftymetallist.csv",
        "Nifty Pharma": "https://nsearchives.nseindia.com/content/indices/ind_niftypharmalist.csv",
        "Nifty PSU Bank": "https://nsearchives.nseindia.com/content/indices/ind_niftypsubanklist.csv",
        "Nifty Private Bank": "https://nsearchives.nseindia.com/content/indices/ind_niftypvtbanklist.csv",
        "Nifty Realty": "https://nsearchives.nseindia.com/content/indices/ind_niftyrealtylist.csv",
        "Nifty Healthcare Index": "https://nsearchives.nseindia.com/content/indices/ind_niftyhealthcarelist.csv",
        "Nifty Consumer Durables": "https://nsearchives.nseindia.com/content/indices/ind_niftyconsumerdurableslist.csv",
        "Nifty Oil & Gas": "https://nsearchives.nseindia.com/content/indices/ind_niftyoilgaslist.csv",
    }

    index_factsheet_urls = {
        "Nifty Auto": "https://www.niftyindices.com/IndexConstituent/ind_niftyautolist.pdf",
        "Nifty Bank": "https://www.niftyindices.com/IndexConstituent/ind_niftybanklist.pdf",
        "Nifty Financial Services": "https://www.niftyindices.com/IndexConstituent/ind_niftyfinancelist.pdf",
        "Nifty FMCG": "https://www.niftyindices.com/IndexConstituent/ind_niftyfmcglist.pdf",
        "Nifty IT": "https://www.niftyindices.com/IndexConstituent/ind_niftyitlist.pdf",
        "Nifty Media": "https://www.niftyindices.com/IndexConstituent/ind_niftymedialist.pdf",
        "Nifty Metal": "https://www.niftyindices.com/IndexConstituent/ind_niftymetallist.pdf",
        "Nifty Pharma": "https://www.niftyindices.com/IndexConstituent/ind_niftypharmalist.pdf",
        "Nifty PSU Bank": "https://www.niftyindices.com/IndexConstituent/ind_niftypsubanklist.pdf",
        "Nifty Private Bank": "https://www.niftyindices.com/IndexConstituent/ind_niftypvtbanklist.pdf",
        "Nifty Realty": "https://www.niftyindices.com/IndexConstituent/ind_niftyrealtylist.pdf",
        "Nifty Healthcare Index": "https://www.niftyindices.com/IndexConstituent/ind_niftyhealthcarelist.pdf",
        "Nifty Consumer Durables": "https://www.niftyindices.com/IndexConstituent/ind_niftyconsumerdurableslist.pdf",
        "Nifty Oil & Gas": "https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.pdf",
    }


class NiftyThematicIndices:
    """Thematic Indices configuration."""

    indices_list = [
        "Nifty Commodities",
        "Nifty India Consumption",
        "Nifty CPSE",
        "Nifty Energy",
        "Nifty Infrastructure",
        "Nifty MNC",
        "Nifty PSE",
        "Nifty Services Sector",
        "Nifty India Digital",
        "Nifty India Manufacturing",
    ]

    index_constituent_list_urls = {
        "Nifty Commodities": "https://nsearchives.nseindia.com/content/indices/ind_niftycommoditieslist.csv",
        "Nifty India Consumption": "https://nsearchives.nseindia.com/content/indices/ind_niftyconsumptionlist.csv",
        "Nifty CPSE": "https://nsearchives.nseindia.com/content/indices/ind_niftycpselist.csv",
        "Nifty Energy": "https://nsearchives.nseindia.com/content/indices/ind_niftyenergylist.csv",
        "Nifty Infrastructure": "https://nsearchives.nseindia.com/content/indices/ind_niftyinfralist.csv",
        "Nifty MNC": "https://nsearchives.nseindia.com/content/indices/ind_niftymnclist.csv",
        "Nifty PSE": "https://nsearchives.nseindia.com/content/indices/ind_niftypse.csv",
        "Nifty Services Sector": "https://nsearchives.nseindia.com/content/indices/ind_niftyservicelist.csv",
        "Nifty India Digital": "https://nsearchives.nseindia.com/content/indices/ind_niftyindiadigitallist.csv",
        "Nifty India Manufacturing": "https://nsearchives.nseindia.com/content/indices/ind_niftyindiamanufacturinglist.csv",
    }

    index_factsheet_urls = {
        "Nifty Commodities": "https://www.niftyindices.com/IndexConstituent/ind_niftycommoditieslist.pdf",
        "Nifty India Consumption": "https://www.niftyindices.com/IndexConstituent/ind_niftyconsumptionlist.pdf",
        "Nifty CPSE": "https://www.niftyindices.com/IndexConstituent/ind_niftycpselist.pdf",
        "Nifty Energy": "https://www.niftyindices.com/IndexConstituent/ind_niftyenergylist.pdf",
        "Nifty Infrastructure": "https://www.niftyindices.com/IndexConstituent/ind_niftyinfralist.pdf",
        "Nifty MNC": "https://www.niftyindices.com/IndexConstituent/ind_niftymnclist.pdf",
        "Nifty PSE": "https://www.niftyindices.com/IndexConstituent/ind_niftypse.pdf",
        "Nifty Services Sector": "https://www.niftyindices.com/IndexConstituent/ind_niftyservicelist.pdf",
        "Nifty India Digital": "https://www.niftyindices.com/IndexConstituent/ind_niftyindiadigitallist.pdf",
        "Nifty India Manufacturing": "https://www.niftyindices.com/IndexConstituent/ind_niftyindiamanufacturinglist.pdf",
    }


class NiftyStrategyIndices:
    """Strategy Indices configuration."""

    indices_list = [
        "Nifty Dividend Opportunities 50",
        "Nifty50 Value 20",
        "Nifty100 Quality 30",
        "Nifty50 Equal Weight",
        "Nifty100 Equal Weight",
        "Nifty100 Low Volatility 30",
        "Nifty Alpha 50",
        "Nifty200 Quality 30",
        "Nifty Alpha Low-Volatility 30",
        "Nifty200 Momentum 30",
    ]

    index_constituent_list_urls = {
        "Nifty Dividend Opportunities 50": "https://nsearchives.nseindia.com/content/indices/ind_niftydividendopps50list.csv",
        "Nifty50 Value 20": "https://nsearchives.nseindia.com/content/indices/ind_nifty50value20list.csv",
        "Nifty100 Quality 30": "https://nsearchives.nseindia.com/content/indices/ind_nifty100quality30list.csv",
        "Nifty50 Equal Weight": "https://nsearchives.nseindia.com/content/indices/ind_nifty50equalweightlist.csv",
        "Nifty100 Equal Weight": "https://nsearchives.nseindia.com/content/indices/ind_nifty100equalweightlist.csv",
        "Nifty100 Low Volatility 30": "https://nsearchives.nseindia.com/content/indices/ind_nifty100lowvolatility30list.csv",
        "Nifty Alpha 50": "https://nsearchives.nseindia.com/content/indices/ind_niftyalpha50list.csv",
        "Nifty200 Quality 30": "https://nsearchives.nseindia.com/content/indices/ind_nifty200quality30list.csv",
        "Nifty Alpha Low-Volatility 30": "https://nsearchives.nseindia.com/content/indices/ind_niftyalphalowvolatility30list.csv",
        "Nifty200 Momentum 30": "https://nsearchives.nseindia.com/content/indices/ind_nifty200momentum30list.csv",
    }

    index_factsheet_urls = {
        "Nifty Dividend Opportunities 50": "https://www.niftyindices.com/IndexConstituent/ind_niftydividendopps50list.pdf",
        "Nifty50 Value 20": "https://www.niftyindices.com/IndexConstituent/ind_nifty50value20list.pdf",
        "Nifty100 Quality 30": "https://www.niftyindices.com/IndexConstituent/ind_nifty100quality30list.pdf",
        "Nifty50 Equal Weight": "https://www.niftyindices.com/IndexConstituent/ind_nifty50equalweightlist.pdf",
        "Nifty100 Equal Weight": "https://www.niftyindices.com/IndexConstituent/ind_nifty100equalweightlist.pdf",
        "Nifty100 Low Volatility 30": "https://www.niftyindices.com/IndexConstituent/ind_nifty100lowvolatility30list.pdf",
        "Nifty Alpha 50": "https://www.niftyindices.com/IndexConstituent/ind_niftyalpha50list.pdf",
        "Nifty200 Quality 30": "https://www.niftyindices.com/IndexConstituent/ind_nifty200quality30list.pdf",
        "Nifty Alpha Low-Volatility 30": "https://www.niftyindices.com/IndexConstituent/ind_niftyalphalowvolatility30list.pdf",
        "Nifty200 Momentum 30": "https://www.niftyindices.com/IndexConstituent/ind_nifty200momentum30list.pdf",
    }


# Valid index categories
VALID_INDEX_CATEGORIES = [
    'BroadMarketIndices',
    'SectoralIndices',
    'ThematicIndices',
    'StrategyIndices',
]
