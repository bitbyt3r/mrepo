#!/usr/bin/python
import os
import sys
from optparse import OptionParser
from lxml import etree as ET
import ConfigParser
import hashlib
import gzip
import shutil
import time

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
  if not(validArgs(arguments)):
    sys.exit("Need help? Try -h. \n")
  groups = []
  categories = []
  
  verbose = False
  if "verbose" in arguments.keys() and arguments['verbose']:
    print "I am in the process of being quite excessively verbose, in case this sentence has not made that entirely apparent."
    verbose = True
  pushgroups = False
  if "pushgroups" in arguments.keys() and arguments['pushgroups']:
    if verbose:
      print "After I am done, I will copy the resulting xml to the repository:",
    if "webdir" in arguments.keys() and arguments['webdir']:
      print arguments['webdir']
    else:
      sys.exit("If you want me to put things in the web directory, you will have to tell me where it is.")
    pushgroups = True
    
  if "groupdir" in arguments.keys() and arguments['groupdir']:
    if verbose:
      print "Fetching group and categories from:", arguments['groupdir']
    groupFiles = getFiles(arguments['groupdir'])
    groups.extend(parseGroupFiles(groupFiles))
    categories.extend(categoriesFromDirs(arguments['groupdir']))
    
  if "rhelcomps" in arguments.keys() and arguments['rhelcomps']:
    if verbose:
      print "Parsing input from XML:", arguments['rhelcomps']
    groups.extend(parseRhelComp(arguments['rhelcomps']))
    categories.extend(categoriesFromXML(arguments['rhelcomps']))
    
  if "excludelist" in arguments.keys() and arguments['excludelist']:
    if verbose:
      print "Excluding all entries in:", arguments['excludelist']
    with open(arguments['excludelist'], "r") as excludeFile:
      excluded = set([x.strip() for x in excludeFile.readlines()])
    for i in groups:
      for j in i['packages']:
        if j in excluded:
          i['packages'].remove(j)
  if verbose:
    print

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
  print
      
  for i in categories:
    if len(i['groups']) == 0:
      categories.remove(i)
      print "Removed %s because it has no groups." % i['name']
    else:
      save = False
      for j in i['groups']:
        if j in [x['name'] for x in groups]:
          save = True
      if not(save):
        categories.remove(i)
        print "Removed %s because all of its groups were removed." % i['name']
  print
        
  categories.sort()
  groups.sort()
  comps = XML_HEADER
  for i in groups:
    if verbose:
      print "@" + i['name']
    comps += genGroupXML(i)
  print
  for i in categories:
    if verbose:
      print "Added category: " + i['name']
    comps += genCategoryXML(i)
  comps += XML_FOOTER
  writeFile(comps, arguments['outfile'])
  print "Output written to: " + arguments['outfile']
  if "listpackages" in arguments.keys() and arguments['listpackages']:
    print
    for i in groups:
      for j in i['packages']:
        print j
  if "listorphans" in arguments.keys() and arguments['listorphans']:
    print
    for i in groups:
      hasParent = False
      for j in categories:
        if i['id'] in j['groups']:
          hasParent = True
      if not(hasParent):
        print i['name'], "has no parents!"
  if pushgroups:
    m = hashlib.sha256()
    with open("arguments['outfile']") as xml:
      fileContents = xml.read()
    m.update(fileContents)
    xmlLength = len(fileContents)
    xmlHash = m.hexdigest()
    with gzip.open("/tmp/comps-file.gz", "wb") as gzippedXMLFile:
      gzippedXMLFile.write(fileContents)
    m = hashlib.sha256()
    with open("/tmp/comps-file.gz") as gzippedXMLFile:
      fileContents = gzippedXMLFile.read()
    m.update(fileContents)
    gzipLength = len(fileContents)
    gzipHash = m.hexdigest()
    
    shutil.copyfile("/tmp/comps-file.gz", arguments['webdir']+"/repodata/"+gzipHash+"-comps-csee.xml.gz")
    shutil.copyfile(arguments['outfile'], arguments['webdir']+"/repodata/"+xmlHash+"-comps-csee.xml")
    tree = ET.parse(arguments['webdir']+"/repodata/repomd.xml")
    root = tree.getroot()
    namespace = "{http://linux.duke.edu/metadata/repo}"
    for i in root.findall(namespace+"data"):
      if i.get("type") == 'group':
        i.find(namespace+"checksum").text = xmlHash
        i.find(namespace+"location").text = "repodata/"+xmlHash+"-comps-csee.xml"
        i.find(namespace+"timestamp").text = "%.2f" % time.time()
        i.find(namespace+"size").text = xmlLength
      if i.get("type") == 'group_gz':
        i.find(namespace+"checksum").text = gzipHash
        i.find(namespace+"open-checksum").text = xmlHash
        i.find(namespace+"location").text = "repodata/"+gzipHash+"-comps-csee.xml.gz"
        i.find(namespace+"timestamp").text = "%.2f" % time.time()
        i.find(namespace+"size").text = gzipLength
    tree.write(arguments['webdir']+"/repodata/repomd.xml", xml_declaration=True, encoding="UTF-8", pretty_print=True)
    if verbose:
      print "Wrote new xml files to:" +  arguments['webdir']+"/repodata/"
    
def validArgs(arguments):
  return True
  
def categoriesFromDirs(directory):
  categories = []
  for i in [name for name in os.listdir(directory) if os.path.isdir(directory+"/"+name) and not(".svn" in name)]:
    category = {}
    category['groups'] = [name for name in os.listdir(directory+"/"+i) if (not(".svn" in name) and not("CategoryDesc.txt" in name) and not(os.path.isdir(directory+"/"+i+"/"+name)))]
    with open(directory + "/" + i + "/CategoryDesc.txt") as categoryDescFile:
      categoryDesc = categoryDescFile.readlines()
      category['id'] = categoryDesc[0].strip()
      category['name'] = categoryDesc[1].strip()
      category['description'] = categoryDesc[2].strip()
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
  for i in category['groups']:
    xml += "     <groupid>" + i + "</groupid>\n"
  xml += "   </grouplist>\n </category>\n"
  return xml
  
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
  parser.add_option('--verbose', '-v', help="Prints a more detailed rendition of what I am doing", action="store_true")
  parser.add_option('--listorphans', '-O', help="lists groups that aren't in any categories", action="store_true")
  parser.add_option('--webdir', '-w', help="The directory of the repository as served by the webserver")
  parser.add_option('--pushgroups', '-p', help="If flagged, apply the resulting xml file to the repository at <webdir>", action="store_true")
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
        group['description'] = groupData.find('description').text
        if not(group['description']):
          group['description'] = "This group needs no description"
        group['name'] = groupData.find('name').text
        # I hate xml...
        # This searches for the packagelist section, and returns the text from every packagereq line
        group['packages'] = [x.text for x in groupData.find('packagelist').findall('packagereq')]
        group['id'] = groupData.find('id').text
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
        if len(lines) < 3:
          sys.exit("Invalid group file: " + filename + "\nIt is too short.")
        name = lines[0].strip()
        description = lines[1].strip()
        packages = [x.strip() for x in lines[2:]]
        groups.append({"id":filename, "name":name, "description":description, "packages":packages})
  return groups
  
def genGroupXML(group):
  xml = " <group>\n"
  xml += "  <id>" + group['id'] + "</id>\n"
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