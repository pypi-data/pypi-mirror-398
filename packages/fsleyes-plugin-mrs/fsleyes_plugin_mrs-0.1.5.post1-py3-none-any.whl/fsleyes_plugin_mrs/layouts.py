#!/usr/bin/env python
#
# controls.py - Contains all Layout formats:
# 1) mrs_fsleyes_layout
#
# Author: Will Clarke <william.clarke@ndcn.ox.ac.uk>
#

from fsleyes import __version__ as fsleyes_version
from fsleyes.layouts import BUILT_IN_LAYOUTS

###############################
# Define a default mrs layout #
###############################

mrs_fsleyes_layout = """
fsleyes.views.orthopanel.OrthoPanel,fsleyes_plugin_mrs.views.MRSView
layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67377088;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=MRSView 2;caption=MRS view 2;state=67377148;dir=2;layer=0;row=1;pos=0;prop=100000;bestw=1296;besth=262;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(2,0,1)=648|
fsleyes.controls.orthotoolbar.OrthoToolBar,fsleyes.controls.overlaydisplaytoolbar.OverlayDisplayToolBar,fsleyes.controls.overlaylistpanel.OverlayListPanel,fsleyes.controls.locationpanel.LocationPanel;syncLocation=True,syncOverlayOrder=True,syncOverlayDisplay=True,syncOverlayVolume=True,movieRate=400,movieAxis=3;showCursor=True,bgColour=#000000ff,fgColour=#ffffffff,cursorColour=#00ff00ff,cursorGap=False,showColourBar=False,colourBarLocation=top,colourBarLabelSide=top-left,showXCanvas=True,showYCanvas=True,showZCanvas=True,showLabels=True,labelSize=12,layout=grid,xzoom=100.0,yzoom=100.0,zzoom=100.0
layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OrthoToolBar;caption=Ortho view toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=607;besth=35;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=11;row=0;pos=0;prop=100000;bestw=922;besth=49;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=201;besth=84;minw=1;minh=1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=201;floath=100;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=383;besth=111;minw=1;minh=1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=383;floath=127;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=139|dock_size(1,10,0)=37|dock_size(1,11,0)=51|
fsleyes_plugin_mrs.controls.MRSToolBar,fsleyes_plugin_mrs.controls.MRSDimControl,fsleyes_plugin_mrs.overlaylistpanel.OverlayListPanel,fsleyes.controls.plotlistpanel.PlotListPanel;;
layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=640;besth=480;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=MRSToolBar;caption=MRS toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=272;besth=34;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=MRSDimControl;caption=NIfTI-MRS;state=67373052;dir=2;layer=0;row=0;pos=0;prop=100000;bestw=188;besth=144;minw=1;minh=1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=188;floath=160;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=2;layer=0;row=0;pos=1;prop=100000;bestw=201;besth=52;minw=1;minh=1;maxw=-1;maxh=-1;floatx=1194;floaty=492;floatw=201;floath=68;notebookid=-1;transparent=255|name=PlotListPanel;caption=Plot list;state=67373052;dir=2;layer=0;row=0;pos=2;prop=100000;bestw=201;besth=52;minw=1;minh=1;maxw=-1;maxh=-1;floatx=1212;floaty=692;floatw=201;floath=68;notebookid=-1;transparent=255|dock_size(5,0,0)=642|dock_size(1,10,0)=36|dock_size(2,0,0)=260|
""".strip()  # noqa: E501
# TODO change this after fsleyes release
# mrs_fsleyes_layout = """
# fsleyes.views.orthopanel.OrthoPanel,fsleyes_plugin_mrs.views.MRSView
# layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67377088;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=MRSView 2;caption=MRS view 2;state=67377148;dir=2;layer=0;row=1;pos=0;prop=100000;bestw=1296;besth=262;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(2,0,1)=648|
# fsleyes.controls.orthotoolbar.OrthoToolBar,fsleyes.controls.overlaydisplaytoolbar.OverlayDisplayToolBar,fsleyes.controls.overlaylistpanel.OverlayListPanel,fsleyes.controls.locationpanel.LocationPanel;syncLocation=True,syncOverlayOrder=True,syncOverlayDisplay=True,syncOverlayVolume=True,movieRate=400,movieAxis=3;showCursor=True,bgColour=#000000ff,fgColour=#ffffffff,cursorColour=#00ff00ff,cursorGap=False,showColourBar=False,colourBarLocation=top,colourBarLabelSide=top-left,showXCanvas=True,showYCanvas=True,showZCanvas=True,showLabels=True,labelSize=12,layout=grid,xzoom=100.0,yzoom=100.0,zzoom=100.0
# layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OrthoToolBar;caption=Ortho view toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=607;besth=35;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=11;row=0;pos=0;prop=100000;bestw=922;besth=49;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=201;besth=84;minw=1;minh=1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=201;floath=100;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=383;besth=111;minw=1;minh=1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=383;floath=127;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=139|dock_size(1,10,0)=37|dock_size(1,11,0)=51|
# fsleyes_plugin_mrs.controls.MRSToolBar,fsleyes_plugin_mrs.controls.MRSDimControl,fsleyes.controls.overlaylistpanel.OverlayListPanel,fsleyes.controls.plotlistpanel.PlotListPanel;;
# layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=640;besth=480;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=MRSToolBar;caption=MRS toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=272;besth=34;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=MRSDimControl;caption=NIfTI-MRS;state=67373052;dir=2;layer=0;row=0;pos=0;prop=100000;bestw=188;besth=144;minw=1;minh=1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=188;floath=160;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=2;layer=0;row=0;pos=1;prop=100000;bestw=201;besth=52;minw=1;minh=1;maxw=-1;maxh=-1;floatx=1194;floaty=492;floatw=201;floath=68;notebookid=-1;transparent=255|name=PlotListPanel;caption=Plot list;state=67373052;dir=2;layer=0;row=0;pos=2;prop=100000;bestw=201;besth=52;minw=1;minh=1;maxw=-1;maxh=-1;floatx=1212;floaty=692;floatw=201;floath=68;notebookid=-1;transparent=255|dock_size(5,0,0)=642|dock_size(1,10,0)=36|dock_size(2,0,0)=260|
# """.strip()  # noqa: E501


# FSLeyes >= 1.8 allows us to specify layouts as entry points (see setup.py).
# In older versions of FSLeyes, we have to abuse the BUILT_IN_LAYOUTS
# to embed an MRS view by default
def parseVersion(version):
    parts = []
    for part in version.split('.'):
        # Give up if we can't parse a component - in case
        # we have a development version, e.g. "2.0.0.dev0"
        try:
            parts.append(int(part))
        except:  # noqa: E722
            break
    return tuple(parts)


if parseVersion(fsleyes_version) < (1, 8, 0):
    BUILT_IN_LAYOUTS.update({'mrs': mrs_fsleyes_layout}) # noqa
