##
# File:  ChemRefDataDepict.py
# Date:  29-Jan-2013
#
# Updates:
#
# 10-Feb-2013 jdw provide encapsulating methods for reusable page sections.
# 12-Fev-2013 jdw share includes with static application pages.
#
##
"""
Base class for HTML depictions containing common HTML constructs using
JQuery UI and SuperFish menus.

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.02"

import os
import sys


class ChemRefDataDepict(object):
    """Base class for HTML depictions contain definitions of common constructs."""

    def __init__(self, includePath=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        """

        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        self.__includePath = includePath
        #
        self.__includeHeadList = ["head_common.html"]
        self.__includeTopList = ["page_header.html", "topmenu.html"]
        self.__includeBottomList = ["page_footer.html"]

        #
        #
        self._pragma = r"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">"""
        self._pragmaXhtml = r"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">"""
        #
        self.__meta = r"""<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />"""

        self._jQueryGenericInclude = r"""

<title>Peptide Reference Dictionary Tools</title>
<link rel="stylesheet" type="text/css"  media="all" href="/birdmodule/styles/general.css" />
<link rel="stylesheet" type="text/css"  media="all" href="/birdmodule/styles/thrColLiqHdr.css" />
<link rel="stylesheet" type="text/css"  media="all" href="/birdmodule/styles/superfish.css"  />
<link rel="stylesheet" type="text/css"  media="all" href="/birdmodule/styles/ui-lightness/jquery-ui-1.8.6.custom.css" />
<script type="text/javascript" src="/birdmodule/js/local/my-utils-1.0.js"></script>
<script type="text/javascript" src="/birdmodule/js/jquery-1.4.4.min.js"></script>
<!--[if IE]><script type="text/javascript" src="/birdmodule/js/excanvas.compiled.js" charset="utf-8"></script><![endif]-->
<script type="text/javascript" src="/birdmodule/js/jquery.hoverIntent.minified.js"></script>
<script type="text/javascript" src="/birdmodule/js/jquery.bgiframe.min.js"></script>
<script type="text/javascript" src="/birdmodule/js/superfish.js"></script>
<script type="text/javascript" src="/birdmodule/js/jquery-ui-1.8.6.custom.min.js"></script>
<script type="text/javascript" src="/birdmodule/js/jquery.corner.js"></script>
"""

        #
        self._jQueryGenericIncludeN = r"""

        <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
        <title>Chemical Reference Data Management Module</title>
        <link rel="stylesheet" type="text/css"  media="all" href="/chem_ref_data_ui/styles/general.css" />
        <link rel="stylesheet" type="text/css"  media="all" href="/chem_ref_data_ui/styles/thrColLiqHdr.css" />
        <link rel="stylesheet" type="text/css"  media="all" href="/chem_ref_data_ui/styles/superfish.css"  />

        <link rel="stylesheet" type="text/css"  media="all" href="/styles/themes/south-street/jquery-ui-1.8.2.custom.min.css" />

        <script type="text/javascript" src="/chem_ref_data_ui/js/my-utils-1.0.js"></script>
        <script type="text/javascript" src="/js/jquery/core/jquery.min.js"></script>
        <script type="text/javascript" src="/js/jquery/ui/jquery-ui.custom.min.js"></script>

        <script type="text/javascript" src="/chem_ref_data_ui/js/jquery/plugins/jquery.form.js"></script>
        <script type="text/javascript" src="/chem_ref_data_ui/js/jquery/plugins/jquery.url.js"></script>


        <link rel="stylesheet" type="text/css" media="all" href="/chem_ref_data_ui/styles/chemrefCommon.css" />



        <script type="text/javascript" src="/chem_ref_data_ui/js/jquery/plugins/jquery.hoverIntent.minified.js"></script>
        <script type="text/javascript" src="/chem_ref_data_ui/js/jquery/plugins/jquery.bgiframe.min.js"></script>
        <script type="text/javascript" src="/chem_ref_data_ui/js/jquery/plugins/superfish.js"></script>

        <script type="text/javascript" src="/chem_ref_data_ui/js/jquery/ui/js/jquery-ui-1.8.20.custom.min.js"></script>
        <script type="text/javascript" src="/chem_ref_data_ui/js/jquery/plugins/jquery.corner.js"></script>

        """

        # <script type="text/javascript" src="/chem_ref_data_ui/js/chemrefCommon.js"></script>

        # ---------------
        self._menuCommonIncludeInline = r"""
        <!-- begin #header-->
        <div id="header">
        <div id="logo"><img src="/images/wwpdb_logo.gif" width="187" height="58" alt="logo" /> </div>
        <div id="headerCont">
                <h1>Chemical Reference Data Management Module</h1>
                <!-- <span id="help_standalone_module" class="ui-icon ui-icon-info fltrgt"></span> -->
                </div>
        <br class="clearfloat" />
        </div>
        <!-- #header ends above-->
        <!-- begin #menu-->
       <div id="menu">
        <ul id="top-menu-options" class="sf-menu">
                <li class="current"> <a href="chemref_index.html" class="first">Home</a> </li>
                <li> <a  href="chemref_search.html">Search</a> </li>
                <li> <a  href="chemref_admin.html">Admin</a>  </li>
                <li> <a  href="chemref_help.html">Help</a> </li>
                <li> <a  href="mailto:jwest@rcsb.rutgers.edu">Feedback</a>  </li>
       </ul>
       </div>
       <!-- #menu ends above-->
       <br class="clearfloat" />
       <br/>
       <!-- END HEADER INCLUDE FILE -->
       """

        #
        self._trailer = r"""
        """
        #
        self._footer_test = r"""
        <!-- BEGIN FOOTER -->
        <br class="clearfloat" />
        <div id="footer">
        <p>&copy; 2013 wwPDB Chemical Reference Data Management Module V0.01</p>
        </div>
        <!-- END   FOOTER -->

        """

    #
    def appDocType(self):
        return self._pragmaXhtml

    def appMetaTags(self):
        return self.__meta

    def appPageTop(self, title=None, scriptPathList=None, cssPathList=None):
        """Return the application specific top of page boiler plate -"""
        oL = []
        oL.append(self.appDocType())
        oL.append('<html xmlns="http://www.w3.org/1999/xhtml">')
        oL.append("<head>")
        if title is not None:
            oL.append("<title>%s</title>" % title)
        try:
            for fn in self.__includeHeadList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        try:
            for pth in cssPathList:
                oL.append('<link rel="stylesheet" type="text/css" media="all" href="%s" />' % pth)
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        try:
            for pth in scriptPathList:
                oL.append('<script type="text/javascript" src="%s"></script>' % pth)
        except:  # noqa: E722 pylint: disable=bare-except
            pass
        oL.append("</head>")

        oL.append('<body class="oneColLiqHdr">')
        try:
            for fn in self.__includeTopList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        oL.append('<br class="clearfloat" />')
        oL.append("<br />")
        oL.append('<div id="mainContent">')
        return oL

    def appPageBottom(self):
        """Return the application specific bottom of page boiler plate -

        </div> <!-- END of mainContent  -->
        <!--#include virtual="includes/page_footer.html"-->
        </body>
        </html>

        """
        oL = []
        oL.append("</div> <!-- END of mainContent  -->")
        try:
            for fn in self.__includeBottomList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()

        except:  # noqa: E722 pylint: disable=bare-except
            pass
        oL.append("</body>")
        oL.append("</html>")
        return oL
