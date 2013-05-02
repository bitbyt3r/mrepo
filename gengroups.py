#!/usr/bin/python
import os
import sys
from optparse import OptionParser
import xml.etree.ElementTree as ET
import collections

XML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE comps PUBLIC "-//Red Hat, Inc.//DTD Comps info//EN" "comps.dtd">
<comps>
"""
XML_FOOTER = """</comps>
"""

def main():
  outFile, groupDir, rhelComps = processArgs()
  if not(outFile) or (not(groupDir) and not(rhelComps)):
    sys.exit("Need help? Try -h. \n")
  #try:
  groups = []
  if groupDir:
    groupFiles = getFiles(groupDir)
    groups.extend(parseGroupFiles(groupFiles))
  if rhelComps:
    groups.extend(parseRhelComp(rhelComps))
  #except Exception:
    #sys.exit("There has been a file error. Please make sure that the files are all valid")

  names = [x['name'] for x in groups]
  d = {}
  for elem in names:
    if elem in d:
      d[elem] += 1
    else:
      d[elem] = 1
  duplicates = [x for x, y in d.items() if y > 1]
  if duplicates:
    print "Error! Duplicates present!"
    for i in duplicates:
      print "There are multiple instances of:", i
    sys.exit("There can only be one of each group name")
  comps = XML_HEADER
  for i in groups:
    print "Adding group: " + i['name']
    comps += genGroupXML(i)
  comps += XML_FOOTER
  writeFile(comps, outFile)
  print "Output written to: " + outFile
  
def processArgs():
  parser = OptionParser(description='Generates group files for yum repositories')
  parser.add_option('--outfile', '-o', help="File to write groups information to")
  parser.add_option('--groupdir', '-g', help="Directory to search for group definition files in")
  parser.add_option('--rhelcomps', '-r', help="Gives me a comps.xml file from redhat to get additional groups from")
  (options, args) = parser.parse_args()
  outFile = options.__dict__['outfile']
  groupDir = options.__dict__['groupdir']
  rhelComps = options.__dict__['rhelcomps']
  return outFile, groupDir, rhelComps
  
def parseRhelComp(rhelComps):
  tree = ET.parse(rhelComps)
  root = tree.getroot()
  groups = []
  if root.tag == "comps":
    for groupData in root:
      if groupData.tag == "group":
	group = {}
	group['name'] = groupData.find('name').text
	group['description'] = groupData.find('name').text
	# I hate xml...
	# This searches for the packagelist section, and returns the text from every packagereq line
	group['packages'] = [x.text for x in groupData.find('packagelist').findall('packagereq')]
	group['filename'] = groupData.find('id').text
	groups.append(group)
  return groups
  
def getFiles(groupDir):
  groupFiles = []
  for root, dirs, files in os.walk(groupDir):
    if not(".svn" in root):
      groupFiles.extend([(root,x) for x in files])
  return groupFiles
  
def parseGroupFiles(groupFiles):
  groups = []
  for root, filename in groupFiles:
    with open(root+"/"+filename, "r") as file:
      lines = file.readlines()
      name = lines[0].strip()
      description = lines[1].strip()
      packages = [x.strip() for x in lines[2:]]
      groups.append({"filename":filename, "name":name, "description":description, "packages":packages})
  return groups
  
def genGroupXML(group):
  xml = " <group>\n"
  xml += "  <id>" + group['filename'] + "</id>\n"
  xml += "  <default>False</default>\n"
  xml += "  <uservisible>True</uservisible>\n"
  xml += "  <name>" + group['name'] + "</name>\n"
  xml += "  <description>" + group['description'] + "</description>\n"
  xml += "   <packagelist>\n"
  for i in group['packages']:
    xml += "    <packagereq type=\"mandatory\">" + i + "</packagereq>\n"
  xml += "   </packagelist>\n"
  xml += " </group>\n"
  return xml
  
def writeFile(comps, outFile):
  with open(outFile, "w") as file:
    for i in comps:
      file.write(i)
  
main()