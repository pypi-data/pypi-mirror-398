##
# File:  ChemRefDataDepictBootstrap.py
# Date:  18-Feb-2013
#
# Updates:
#
#
##
"""
Base class for HTML depictions containing common HTML constructs using
BootStrap and

"""
__docformat__ = "restructuredtext en"
__author__ = "John Westbrook"
__email__ = "jwest@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.02"

import os
import sys


class ChemRefDataDepictBootstrap(object):
    """Base class for HTML depictions contain definitions of common constructs
    using HTML5 and Bootstrap CSS -

    """

    def __init__(self, includePath=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        """

        :param `verbose`:  boolean flag to activate verbose logging.
        :param `log`:      stream for logging.

        """
        self.__includePath = includePath
        #
        # Within the <head></head> section
        self.__includeHeadList = ["head_common_bs.html"]
        # At the beginning of the <body>
        self.__includeTopList = ["page_header_bs.html"]
        #
        self.__includeBottomList = ["page_footer_bs.html"]
        #
        self.__includeJavaScriptList = ["page_javascript_bs.html"]
        #
        self.__meta = r"""<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />"""

    #
    def appDocType(self):
        return "<!DOCTYPE html>"

    def appMetaTags(self):
        return self.__meta

    def appPageTop(self, title=None, cssPathList=None):
        """Return the application specific top of page boiler plate -"""
        oL = []
        oL.append("<!DOCTYPE html>")
        oL.append('<html lang="en"')
        oL.append("<head>")
        try:
            for fn in self.__includeHeadList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        #
        # include application specific CSS files --
        try:
            for pth in cssPathList:
                oL.append('<link rel="stylesheet" type="text/css" media="all" href="%s" />' % pth)
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        if title is not None:
            oL.append("<title>%s</title>" % title)

        oL.append("</head>")
        #
        oL.append("<body>")

        oL.append('<div id="wrap">')
        try:
            for fn in self.__includeTopList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        oL.append('<div class="container">')

        oL.append("<!-- # Application content begins here -->")

        return oL

    def appPageBottom(self, scriptPathList=None):
        """Return the application specific bottom of page boiler plate -

        <!--#include virtual="includes/page_footer.html"-->
        </div> <!-- end container -->

        <!--#include virtual="includes/page_javascript_bs.html"-->
        <script ... app specific script files > </script>

        </body>
        </html>

        """
        oL = []
        oL.append("</div> <!-- end of application content  -->")
        oL.append("</div> <!-- end of wrapper  -->")

        # oL.append('</div> <!-- end container -->')
        try:
            for fn in self.__includeJavaScriptList:
                pth = os.path.join(self.__includePath, fn)
                ifh = open(pth, "r")
                oL.append(ifh.read())
                ifh.close()
        except:  # noqa: E722 pylint: disable=bare-except
            pass

        try:
            for pth in scriptPathList:
                oL.append('<script type="text/javascript" src="%s"></script>' % pth)
        except:  # noqa: E722 pylint: disable=bare-except
            pass

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
