#!/usr/bin/env python

"""allegro2svg.py: Convert Allegro element data into flexible SVG."""

__author__      = "Kevin Cook"
__copyright__   = "Copyright 2002, 2006, 2014, Kevin Cook"

# This utility has roots streching back to perl5 scripts and Excel sheets I made for Mentor Graphics.

import sys
import re
import tkinter as tk

csvDelim = ';'

itemData = {}
columnSet = set()

def parse_Allegro_Show_Element(raw_string):

    listingReportedTotal = 0

    itemIndex = 0
    itemType = ''
    itemContent = ''

    currentLayer = ''
    currentNetName = ''

    REanyNL = re.compile(r"(\n|\r|\r\n)")

    REsubclass = re.compile(r"""
	 \s* subclass \s* (?P<subclass>.*) \s*
	""",re.VERBOSE)

    REnetname = re.compile(r"""
	 \s* part \s of \s net \s name\: \s* (?P<netname>.*) \s*
	""",re.VERBOSE)

    RElisting = re.compile(r"""
	 \s* LISTING\: \s (?P<listingReportedTotal>\d+) \s element .*
	""",re.VERBOSE)
	
    REitemSplit = re.compile(r"""
     (?: ^\s* ~~~~~~ .* \n
	 ^\s* \n )?
	 ^\s* Item
	""",re.VERBOSE|re.MULTILINE)

    REconnectLineHeader = re.compile(r"""
	 \s* (?P<ItemIndex>\d+) \s* \< \s CONNECT \s LINE \s \> \s* \n
     ^\s* \n 
     ^\s* class    \s* (?P<clClass>.*) \s* \n
     ^\s* subclass \s* (?P<clSubclass>.*) \s* \n 
     ^\s* \n 
     ^\s* part \s of \s net \s name \: \s* (?P<clNetName>.*) \s* \n
     ^\s* Length \: \s* (?P<clLength>\d+\.?\d*) \s* (?P<clLengthUnit>.*) \s* \n 
     ^\s* \n 	 
     ( ( ^\s* Net \s path \s data \s* .* \n ) |

     ( ^\s* Net \s path \s length \: \s* (?P<clNetPathLength>\d+\.?\d*) \s* (?P<clNetPathLengthUnit>.*) \s* \n
       ^\s* Total \s manhattan \s length \: \s* (?P<clTotalManhattanLength>\d+\.?\d*) \s* (?P<clTotalManhattanLengthUnit>.*) \s* \n
       ^\s* Percent \s manhattan \: \s* (?P<clPercentManhattan>\d+\.?\d*) \% \s* \n ) )
	""",re.VERBOSE|re.MULTILINE)

    REconnection = re.compile(r"""
	 ^\s* (?P<type>.*)
	 \s at \s xy
	 \s \( (?P<X>\d+\.\d+)
	 \s    (?P<Y>\d+\.\d+) \) .*
	""",re.VERBOSE)

    REsegmentSplit = re.compile(r"""
	 ^segment:
	""",re.VERBOSE|re.MULTILINE)

    REsegment = re.compile(r"""
	 \s? xy
	 \s \( (?P<fromX>\d+\.\d+)
	 \s    (?P<fromY>\d+\.\d+) \)
	 \s xy
	 \s \( (?P<toX>\d+\.\d+)
	 \s    (?P<toY>\d+\.\d+)   \)
	 \s width
	 \s \( (?P<width>\d+\.\d+) \) .*
	""",re.VERBOSE)

    def XYtuplesToSVGpath(listOfTuples):
        ret = ''
        for point in listOfTuples:
            ret += (' ' + str(point[0]) + ',' + str(point[1]))
            # should add a failsafe test here verifying that the width in this segment hasn't changed
        return ("\"M" + ret + "\"")


    clean_string = REanyNL.sub('\n', raw_string)
	
    itemIndex = 0	
    #itemData = {}
    #columnSet = set()
    pathIdSet = set()

    for item in re.split(REitemSplit,clean_string,0):
        itemIndex = 0		
        m = REconnectLineHeader.match(item)
        if m:
            itemIndex = int(m.group('ItemIndex'))
            for k in m.groupdict().keys():
                if m.group(k) is not None:
                    columnSet.add(k)
                    itemData.setdefault(itemIndex,{})[k] = m.group(k)		
        else:
             #print ('something is amiss: ' + item)
             continue

        i = 0
        for line in item.splitlines():  # dirty hack because I can't get multiline to work on this one
            m = REconnection.match(line)
            if m:
                i += 1
                for k in m.groupdict().keys():
                    composite = 'connection' + '{:02d}'.format(i) + '-' + k
                    columnSet.add(composite)	
                    itemData.setdefault(itemIndex,{})[composite] = m.group(k)		

        ## segments

        segmentIndex = 0
        vertexListChunkIndex = 1
        vertexList = []
        segmentKey = ''
        for segment in re.split(REsegmentSplit,item,0):
            m = REsegment.match(segment)
            if m:

                ## names for dictionary
                pathIdKey = 'aSVGpath' + '{:02d}'.format(vertexListChunkIndex) + '.id'
                pathVertexListKey = 'aSVGpath' + '{:02d}'.format(vertexListChunkIndex) + '.vertexlist'
                pathWidthKey = 'aSVGpath' + '{:02d}'.format(vertexListChunkIndex) + '.width'

                segmentIndex += 1
                for k in m.groupdict().keys():
                    segmentKey = 'segment' + '{:02d}'.format(segmentIndex) + '-' + k
                    columnSet.add(segmentKey)	
                    itemData.setdefault(itemIndex,{})[segmentKey] = m.group(k)

                tailVertex = (m.group('fromX'),m.group('fromY'),m.group('width'))
                headVertex = (m.group('toX'),m.group('toY'),m.group('width'))
                if not vertexList:
                    vertexList.append(tailVertex)
                    vertexList.append(headVertex)
                elif tailVertex == vertexList[-1]:
                    vertexList.append(headVertex)                    
                else: # if we got here there was a change in width
                    i = 0
                    while True:
                        i+= 1
                        pathId = (itemData[itemIndex]['clSubclass'] + '-' + itemData[itemIndex]['clNetName'] + '-track' + '{:03d}'.format(i))
                        if pathId not in pathIdSet:
                            break
                    pathIdSet.add(pathId)
                    itemData.setdefault(itemIndex,{})[pathIdKey] = pathId
 
                    itemData.setdefault(itemIndex,{})[pathVertexListKey] = XYtuplesToSVGpath(vertexList)
                    itemData.setdefault(itemIndex,{})[pathWidthKey] = vertexList[-1][2]
                    columnSet.add(pathVertexListKey)	
                    columnSet.add(pathWidthKey)	
                    vertexListChunkIndex += 1
                    vertexList.clear()
                    vertexList.append(tailVertex)
                    vertexList.append(headVertex)

        i = 0
        while True:
            i+= 1
            pathId = (itemData[itemIndex]['clSubclass'] + '-' + itemData[itemIndex]['clNetName'] + '-track' + '{:03d}'.format(i))
            if pathId not in pathIdSet:
                break
        pathIdSet.add(pathId)
        itemData.setdefault(itemIndex,{})[pathIdKey] = pathId

        itemData.setdefault(itemIndex,{})[pathVertexListKey] = XYtuplesToSVGpath(vertexList)
        itemData.setdefault(itemIndex,{})[pathWidthKey] = vertexList[-1][2]
        columnSet.add(pathIdKey)	
        columnSet.add(pathVertexListKey)	
        columnSet.add(pathWidthKey)	


def dump_csv():

    print (csvDelim.join(sorted(columnSet)))
    for i in sorted(itemData):
        for j in sorted(columnSet):
            #dirty = str(itemData.get(i).get(j,''))
            #print (dirty.rstrip() + csvDelim, end='')
            print (  str(itemData.get(i).get(j,'')) + csvDelim, end='')
        print ('')


# here is the GUI version for grabbing the clipboard and processing on a button click 

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.grab_clip_b = tk.Button(self)
        self.grab_clip_b["text"] = "grab clipboard"
        self.grab_clip_b["command"] = self.grab_clip
        self.grab_clip_b.pack(side="top")

        self.QUIT = tk.Button(self, text="QUIT", fg="red",command=root.destroy)
        self.QUIT.pack(side="bottom")

    def grab_clip(self):
        print ("button press\n")
        dump_text = root.clipboard_get()
        parse_Allegro_Show_Element(dump_text)
        dump_csv()

# finally the main body, if an input file is specified, try to open it, otherwise use the GUI 

if len(sys.argv) == 2: 
    try:
        f = open(str(sys.argv[1]))
    except:
        print('could not open ' + str(sys.argv[1])) 
        sys.exit(-1) 
    dump_text = f.read()
    f.close()
    parse_Allegro_Show_Element(dump_text)
    dump_csv()
    sys.exit(0) 
else:
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

### TODO
### make path creation generic (don't store directly as svg m .... etc: one column for id, one for path, one for width (another one for layer?)
### take path creation out of parse_Allegro_Show_Element()
### storage of numeric objects as strings
### output hybrid CSV XML
### output numerics with something "+" "-" E0... ?? so that gnumeric doesn't interpret as dates

