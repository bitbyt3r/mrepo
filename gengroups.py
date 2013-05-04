#!/usr/bin/python
import os
import sys
from optparse import OptionParser
import xml.etree.ElementTree as ET
import ConfigParser

XML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE comps PUBLIC "-//Red Hat, Inc.//DTD Comps info//EN" "comps.dtd">
<comps>
"""
XML_FOOTER = """</comps>
"""
DEFAULT_CONFIG_FILE = "./groups.conf"


def main():
  if processArgs():
    arguments = processArgs()
  arguments = parseConfigFile(arguments)
  print arguments
  if not(validArgs(arguments)):
    sys.exit("Need help? Try -h. \n")
  groups = []
  categories = []
  if "groupdir" in arguments.keys() and arguments['groupdir']:
    groupFiles = getFiles(arguments['groupdir'])
    groups.extend(parseGroupFiles(groupFiles))
    categories.extend(categoriesFromDirs(arguments['groupdir'])
  if "rhelcomps" in arguments.keys() and arguments['rhelcomps']:
    groups.extend(parseRhelComp(arguments['rhelcomps']))
    categories.extend(categoriesFromXML(arguments['rhelcomps'])
  if "excludelist" in arguments.keys() and arguments['excludelist']:
    with open(arguments['excludelist'], "r") as excludeFile:
      excluded = set([x.strip() for x in excludeFile.readlines()])
    for i in groups:
      for j in i['packages']:
        if j in excluded:
          i['packages'].remove(j)

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
    
  for i in groups:
    if len(i['packages']) == 0:
      groups.remove(i)
      print "Removed %s because it has no packages." % i['name']
    
  comps = XML_HEADER
  for i in groups:
    print "@" + i['name']
    comps += genGroupXML(i)
  for i in categories:
    print "Added category: " + i.keys()[0]
    comps += genCategoryXML(i)
  comps += XML_FOOTER
  writeFile(comps, arguments['outfile'])
  print "Output written to: " + arguments['outfile']
  if "listpackages" in arguments.keys() and arguments['listpackages']:
    for i in groups:
      for j in i['packages']:
        print j
  
def validArgs(arguments):
  return True
  
def categoriesFromDirs(directory):
  categories = []
  for i in [name for name in os.listdir(directory) if os.path.isdir(name) and not(".svn" in name)]:
    category = {}
    category['grouplist'] = [name for name in os.listdir(directory+"/"+name) if not(".svn" in name)]
    with open(directory+"/"+name+"/CategoryDesc.txt") as categoryDescFile:
      category['id'] = categoryDescFile.read().strip()
      category['name'] = categoryDescFile.read().strip()
      category['description'] = categoryDescFile.read().strip()
      categoryDescFile.close()
    categories.append(category)
  return categories
  
def categoriesFromXML(rhelComps):
  tree = ET.parse(rhelComps)
  root = tree.getroot()
  categories = []
  if root.tag == "comps":
    for categoryData in root:
      if categoryData.tag == "category":
        category = {}
        category['groups'] = [x.text for x in categoryData.find('grouplist').findall('groupid')]
        category['name'] = categoryData.find('name').text
        category['id'] = categoryData.find('id').text
        category['description'] = categoryData.find('description').text
        categories.append(category)
  return categories
  
def genCategoryXML(category):
  xml = " <category>\n"
  xml += "   <id>" + category['id'] + "</id>\n"
  xml += "   <name>" + category['name'] + "</name>\n"
  xml += "   <description>" + category['description'] + "</description>\n"
  xml += "   <grouplist>\n"
  for i in category.keys['groups']:
    xml += "     <groupid>" + i + "</groupid>\n"
  xml += "   </grouplist>\n </category>\n"
  
def parseConfigFile(arguments):
  config = ConfigParser.ConfigParser()
  config.readfp(open(DEFAULT_CONFIG_FILE, "r"))
  if config.has_section("main"):
    for i in arguments.keys():
      if config.has_option("main", i) and config.get("main", i) and not(arguments[i]):
        arguments[i] = config.get("main", i)
  return arguments
  
def processArgs():
  parser = OptionParser(description='Generates group files for yum repositories')
  parser.add_option('--outfile', '-o', help="File to write groups information to")
  parser.add_option('--groupdir', '-g', help="Directory to search for group definition files in")
  parser.add_option('--rhelcomps', '-r', help="Gives me a comps.xml file from redhat to get additional groups from")
  parser.add_option('--listpackages', '-l', help="Prints a list of every package listed in a group", action="store_true")
  parser.add_option('--excludelist', '-e', help="File that contains a list of packages to exclude from all groups")
  (options, args) = parser.parse_args()
  return options.__dict__
  
def parseRhelComp(rhelComps):
  tree = ET.parse(rhelComps)
  root = tree.getroot()
  groups = []
  if root.tag == "comps":
    for groupData in root:
      if groupData.tag == "group":
        group = {}
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
    if not("CategoryDesc.txt" in filename):
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