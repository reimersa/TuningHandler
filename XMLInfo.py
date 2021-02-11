import os, sys
import xml.dom.minidom as minidom
import subprocess
import StringIO
import xml.sax
from copy import deepcopy

class XMLInfo:
    def __init__(self, xmlfilename):
        self.xmlfilename = xmlfilename
        self.document = minidom.parse(xmlfilename)


    def print_module_children_attributes(self):
        for e in [n for n in self.document.getElementsByTagName('Hybrid')[0].childNodes if n.nodeType is minidom.Node.ELEMENT_NODE]: print e.attributes.items()

    def save_xml_as(self, outfilename):
        with open(outfilename, 'wr') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>')
            f.write(self.document.documentElement.toxml())


    def set_module_attribute_by_moduleid(self, moduleID, attributename, value):
        for m in self.document.getElementsByTagName('Hybrid'):
            if m.getAttribute('Id') == str(moduleID):
                m.setAttribute(attributename, str(value))



    def set_module_attribute_by_modulename(self, modulename, attributename, value):
        for m in self.document.getElementsByTagName('Hybrid'):
            c = [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53'][0]
            if get_modulename_from_txtfilename(c.getAttribute('configfile')) == modulename:
                m.setAttribute(attributename, str(value))



    def set_txtfilepath_by_moduleid(self, moduleID, txtfilepath):
        for m in self.document.getElementsByTagName('Hybrid'):
            if m.getAttribute('Id') == str(moduleID):
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53_Files']:
                    c.setAttribute('path', txtfilepath)



    def set_txtfilepath_by_modulename(self, modulename, txtfilepath):
        for m in self.document.getElementsByTagName('Hybrid'):
            c = [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53'][0]
            if get_modulename_from_txtfilename(c.getAttribute('configfile')) == modulename:
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53_Files']:
                    c.setAttribute('path', txtfilepath)



    def set_chip_attribute_by_moduleid(self, moduleID, chipID, attributename, value):
        for m in self.document.getElementsByTagName('Hybrid'):
            if m.getAttribute('Id') == str(moduleID):
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53']:
                    if c.getAttribute('Id') == str(chipID):
                        c.setAttribute(attributename, str(value))



    def set_chip_attribute_by_modulename(self, modulename, chipID, attributename, value):
        for m in self.document.getElementsByTagName('Hybrid'):
            c = [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53'][0]
            if get_modulename_from_txtfilename(c.getAttribute('configfile')) == modulename:
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53']:
                    if c.getAttribute('Id') == str(chipID):
                        c.setAttribute(attributename, str(value))



    def set_chip_setting_by_moduleid(self, moduleID, chipID, attributename, value):
        for m in self.document.getElementsByTagName('Hybrid'):
            if m.getAttribute('Id') == str(moduleID):
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53']:
                    if c.getAttribute('Id') == str(chipID):
                        settings = [n for n in c.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'Settings'][0]
                        settings.setAttribute(attributename, str(value))




    def set_chip_setting_by_modulename(self, modulename, chipID, attributename, value):
        for m in self.document.getElementsByTagName('Hybrid'):
            c = [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53'][0]
            if get_modulename_from_txtfilename(c.getAttribute('configfile')) == modulename:
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53']:
                    if c.getAttribute('Id') == str(chipID):
                        settings = [n for n in c.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'Settings'][0]
                        settings.setAttribute(attributename, str(value))


    def copy_chip_by_moduleid(self, moduleID, sourcechipID, targetchipID):

        #check if target chip exists, then throw error
        for m in self.document.getElementsByTagName('Hybrid'):
            if m.getAttribute('Id') == str(moduleID):
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53']:
                    if c.getAttribute('Id') == str(targetchipID):
                        raise AttributeError('in copy_chip_by_moduleid(): tried to generate chip with ID that already exists. Abort.')

                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53']:
                    if c.getAttribute('Id') == str(sourcechipID):
                        newchip = c.cloneNode(deep=True)
                        newchip.setAttribute('Id', str(targetchipID))
                        m.appendChild(newchip)
                        return


    def copy_module_by_moduleid(self, sourcemoduleID, targetmoduleID):

        #check if target chip exists, then throw error
        for m in self.document.getElementsByTagName('Hybrid'):
            if m.getAttribute('Id') == str(targetmoduleID):
                raise AttributeError('In copy_module_by_moduleid(): tried to generate module with ID that already exists. Abort.')

        for m in self.document.getElementsByTagName('Hybrid'):
            if m.getAttribute('Id') == str(sourcemoduleID):
                newmodule = m.cloneNode(deep=True)
                newmodule.setAttribute('Id', str(targetmoduleID))
                m.parentNode.appendChild(newmodule)
                return
        raise AttributeError('In copy_module_by_moduleid(): did not find source module ID %s' % (str(sourcemoduleID)))


    def keep_only_chips_by_moduleid(self, moduleID, chiplist):
        for m in self.document.getElementsByTagName('Hybrid'):
            if m.getAttribute('Id') == str(moduleID):
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53']:
                    if int(c.getAttribute('Id')) not in chiplist:
                        m.removeChild(c)


    def keep_only_chips_by_modulename(self, modulename, chiplist):
        for m in self.document.getElementsByTagName('Hybrid'):
            ch = [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53'][0]
            if get_modulename_from_txtfilename(ch.getAttribute('configfile')) == modulename:
                for c in [n for n in m.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'RD53']:
                    if int(c.getAttribute('Id')) not in chiplist:
                        m.removeChild(c)

    def keep_only_modules_by_moduleid(self, modulelist):
        for m in self.document.getElementsByTagName('Hybrid'):
            if int(m.getAttribute('Id')) not in modulelist:
                m.parentNode.removeChild(m)




    def set_daq_settings(self, settingname, value):
        settings_mother = [n for n in self.document.childNodes[0].childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'Settings'][0]
        for setting in [n for n in settings_mother.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'Setting']:
            if setting.getAttribute('name') == settingname:
                setting.childNodes[0].data = value
                return

        #arriving here means no setting with the desired name exists. Create one.
        newsetting = self.document.createElement('Setting')
        settings_mother.appendChild(newsetting)
        newsetting.setAttribute('name', settingname)
        newvalue = self.document.createTextNode(value)
        newsetting.appendChild(newvalue)
        return


    def print_daq_settings(self):
        settings_mother = [n for n in self.document.childNodes[0].childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'Settings'][0]
        for setting in [n for n in settings_mother.childNodes if n.nodeType is minidom.Node.ELEMENT_NODE and n.tagName == 'Setting']:
            print setting.getAttribute('name'), setting.childNodes[0].data




def get_modulename_from_txtfilename(txtfilename):
    for part in txtfilename.split('_'):
        if 'mod' in part:
            return part
    return None



#
