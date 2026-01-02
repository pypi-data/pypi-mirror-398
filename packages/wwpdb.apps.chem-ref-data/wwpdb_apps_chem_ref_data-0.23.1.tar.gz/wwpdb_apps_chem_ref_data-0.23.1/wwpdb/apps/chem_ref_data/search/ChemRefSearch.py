##
# File:  ChemRefSearch.py
# Date:  22-Apr-2010 J. Westbrook
#
# Update:
#
##
"""
Chemical reference search general implementation -

"""

import sys

from wwpdb.apps.chem_ref_data.search.ChemRefSearchBase import ChemRefSearchBase
from wwpdb.apps.chem_ref_data.search.ChemRefSearchDef import ChemRefSearchDef


class ChemRefSearch(ChemRefSearchBase):
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        super(ChemRefSearch, self).__init__(siteId=siteId, verbose=verbose, log=log)
        #
        self.set(ChemRefSearchDef._displayTypeDict, ChemRefSearchDef._keyDict, ChemRefSearchDef._searchTypeDict, ChemRefSearchDef._queryTypeDict)
        #
