#!/bin/env python
# -*- coding: utf-8 -*-
#Author: Pierre Ratinaud
#Copyright (c) 2008-2009, Pierre Ratinaud
#Lisense: GNU/GPL

import urllib2
import socket
import wx
   
def NewVersion(parent):
    version = parent.version.split(' ')
    if len(version) == 3:
        versionnb = float(version[0])
        versionsub = int(version[2])
    else:
        versionnb = float(version[0])
        versionsub = False
    erreur = False
    new = False
    req = urllib2.Request("http://www.iramuteq.org/current_version")
    try:
        LastVersion = urllib2.urlopen(req,'',3)
        lastversion = LastVersion.readlines()
        lastversion = lastversion[0].replace('\n', '').split('-')
        if len(lastversion) == 2 :
            if (float(lastversion[0]) > versionnb) :
                new = True
            elif float(lastversion[0]) == versionnb and versionsub :
                if versionsub < int(lastversion[1].replace('alpha', '')):
                    new = True
        elif len(lastversion) == 1 :
            if (float(lastversion[0]) >= versionnb) and (versionsub) :
                new = True
            elif (float(lastversion[0]) > versionnb) and not versionsub :
                new = True
    except :
        erreur = u"la page n'est pas accessible"
    if not erreur and new :
        msg = u"""
Une nouvelle version d'IRaMuTeQ (%s) est disponible.
Vous pouvez la télécharger à partir du site web iramuteq :
http://www.iramuteq.org""" % '-'.join(lastversion)
        dlg = wx.MessageDialog(parent, msg, u"Nouvelle version disponible", wx.OK | wx.NO_DEFAULT | wx.ICON_WARNING)
        dlg.CenterOnParent()
        if dlg.ShowModal() in [wx.ID_NO, wx.ID_CANCEL]:
             evt.Veto()

#print NewVersion('0.1-alpha18')
