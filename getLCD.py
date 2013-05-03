#!/usr/bin/python
# This will take a list of packages and return the packages that aren't
# depended on by other packages in the list, i.e. the lowest common
# denominator needed to get yum to install the other packages.
import os
import rpm
import sys

def main():
  packagereqs = {}
  packagepros = {}

  notKept = open("notKept")
  checkList = [x.strip() for x in notKept.readlines()]
  notKept.close()
  
  grouped = open("grouped")
  groupedList = [x.strip() for x in grouped.readlines()]
  checkList.extend(groupedList)
  grouped.close()
  
  ts = rpm.TransactionSet()
  for i in checkList:
    mi = ts.dbMatch('name', i)
    packagereqs[i] = []
    packagepros[i] = []
    for ind in range(mi.count()):
	h = mi.next()
	for dep in h[rpm.RPMTAG_REQUIRENAME]:
          if not("/" in dep):
            packagereqs[i].append(dep.split("(")[0])
        for pro in h[rpm.RPMTAG_PROVIDENAME]:
          if not("/" in pro):
            packagepros[i].append(pro.split("(")[0])
    packagepros[i].append(i)
    packagereqs[i] = set(packagereqs[i])
    packagepros[i] = set(packagepros[i])
	    
  needed = {}
  for i in checkList:
    needed[i] = True

  for i in checkList:
    for j in checkList:
      if not(i == j):
        for k in packagepros[i]:
          if k in packagereqs[j]:
            needed[i] = False
  for i in needed.keys():
    if needed[i]:
      print i
main()
