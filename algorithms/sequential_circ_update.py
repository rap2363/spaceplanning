import math
import matplotlib.pyplot as plt
import random
import copy
#from Grasshopper import DataTree as tree
#import ghpythonlib.components as ghcomp
#import ghpythonlib.parallel
#import Rhino.Geometry as geometry

## GH Global Output Arrays


objType = [];
objX = [];
objY = [];
objL = [];
objH = [];

## PARAMETERS ######################################################################################
decay = 1;
C_Block = 2;
C_Power = .6;
DL_Influence = 18;
X_dim = 100;
Y_dim = 65;
##
DECAY = decay;                          # Decay length for fields. Increase to extend influence of
                                        # element fields
CIRCULATION_BLOCK = int(C_Block);       # Amount of circulation generated by an object
CIRCULATION_MAX_VALUE = C_Power;        # Maximum blocking value
DAYLIGHT_INFLUENCE = DL_Influence;      # Extent of Daylight Influence
ELEMENT_MAX_VALUE = 1000;
THRESH = 1;
showDisplay = True;                     # Toggle to False in Grasshopper
L = int(X_dim);                         # Length of Floorplate
H = int(Y_dim);                         # Height of Floorplate

#    Office(0), WS(1), CL(2), CS(3), PS(4), E(5), S(6), R(7)
A = [
    [-1, 0.7, 0.9, 0.6, 0.3, 0.0, 0.0, 0.0],
    [0.7, .7, 0.3, 0.9, 0.2, 0.0,  0.0,  -0.8],
    [0.9, 0.3,-0.8, 0.5, 0.8, 0.8, 0.8, 0.4],
    [0.6, 0.9, 0.5, -0.2, 0.1, 0.6, 0.6, 0.0],
    [0.3, 0.2, 0.8, 0.1, 0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.8, 0.6, 0.0, 0.0, 1.0, 0.6],
    [0.0, 0.0, 0.8, 0.6, 0.0,  1.0, 0.0, 0.7],
    [0.0, -0.8, 0.4, 0.0, 0.0, 0.6, 0.7, 0.0]
];
lhArray = [
            [9, 11],
            [6, 8],
            [12, 17],
            [10, 10],
            [7, 7],
            [14, 17],
            [18, 11],
            [19, 13]];
alphaVals = [.8, .5, 1, .6, 0, .9, .9, .9];
#alphaVals = [.5, .3, .8, .4, 0, .5, .5, .5];
elementLabels = ['Of.', 'WS', 'Lg. Conf', 'Sm. Conf', 'PS', 'Elev', 'Stairs', 'RR'];
daylightAdj = [0.6, 0.9, 0.5, 0.4, 0, 0, 0, 0];
centerFieldAdj = [-.6, -.6, -.4, -.1, .3, .9, .9, .9];
numElements = len(A[0]);
####################################################################################################
def runScript():
    ## Initialization
    env = Environment(L,H);
    hm = HeatMap(env, numElements);
    hm.addDaylightField([2, 3]);
    hm.addCenterField();
    ########### Grouping
    numLargeConfRooms = 3;
    pregroup        = [[7,1],[5,1],[6,1], [1, 40]];
    groupOrder      = [2, 0, 3, 4, 5, 6, 7,1];
    postgroup = [];
    totalToPlace    = [10, 40, 3, 6, 3, 1, 1, 1];
    elemsToPlace = calculateTotalElementOrderArray(pregroup, groupOrder, postgroup, totalToPlace);
    ########### Placement
    elemsToDraw = [];
    count = 0;
    for j,e in enumerate(elemsToPlace):
        scaleVector = A[e[2]];
        plt.hold(True);
        for i in range(int(e[3])):
            [x, y, l, h] = findBestOrientation(hm, e[0], e[1], e[2], checkAll=False);
            elemsToDraw.append([x, y, l, h, e[2], j]);
            elem = Element(x, y, l, h, e[2], count);
            hm.env.elementList[count] = elem;
            displayMat(hm, e[2], elemsToDraw, count);
            print e[2], count;
            objType.append(elem.elemType);
            objX.append(elem.x);
            objY.append(elem.y);
            objL.append(elem.l);
            objH.append(elem.h);
            hm.populateField([elem]);
            hm.addCirculation(elem);
            count += 1;
    displayMat(hm, e[2], elemsToDraw, count);
    print 'Grossing Factor: '+str(grossingFactor(hm.env))+'%';

## Calculate Grossing Factor
def grossingFactor(env):
    unocc = 0;
    for i in range(env.ylen):
        for j in range(env.xlen):
            if(not(env.grid[i][j]['occupied'])):
                unocc += 1;
    return 100*(unocc/float(X_dim*Y_dim));

## Find the best orientation for the element
def findBestOrientation(heatmap, x0, y0, elemType, checkAll = False):
    bestVal = -float('inf');
    bestOr = [-1,-1,-1,-1];
    delta = abs(x0-y0);
    if(checkAll):
        r = 1;
    else:
        r = delta;
    if(x0 < y0):
        for delt in range(0, delta+1, r):
            x = x0 + delt;
            y = y0 - delt;
            [[ey,ex],val] = heatmap.maximizeConvolvedHeatMap(x,y,elemType);
            if(val > bestVal):
                bestVal = val;
                bestOr = [ex,ey,x,y];
    else:
        for delt in range(0,delta+1,max(r,1)):
            x = x0 - delt;
            y = y0 + delt;
            [[ey, ex], val] = heatmap.maximizeConvolvedHeatMap(x,y,elemType);
            if(val > bestVal):
                bestVal = val;
                bestOr = [ex,ey,x,y];
    return bestOr;

## Draws objects
def drawObs(obs,col):
    for ob in obs:
        plt.plot([ob[0]-.5, ob[0]+ob[2]-.5, ob[0]+ob[2]-.5, ob[0]-.5, ob[0]-.5],[ob[1]-.5, ob[1]-.5, ob[1]-.5+ob[3], ob[1]-.5+ob[3], ob[1]-.5],'k-');
        #plt.text(ob[0]+0.25*ob[2], ob[1]+0.5*ob[3], elementLabels[ob[4]]+str(ob[5]),fontsize=10);
        plt.text(ob[0]+0.25*ob[2], ob[1]+0.5*ob[3], elementLabels[ob[4]],fontsize=10,color = col);

## Displays the heat map (matrix)
def displayMat(heatMap, elemType, obs, n):
    m = thresholdMapData(heatMap.returnHeatMapData(elemType), THRESH);
    plt.imshow(m);
    plt.hold(True);
    plt.matshow(m, cmap = 'RdYlGn');
    plt.xlim(0,L);
    plt.ylim(0,H);
    drawObs(obs,'white');
    plt.savefig('/Users/rohan/Documents/Vannevar/spaceplanning/sequentialplots/im'+str(n)+'.png');

## Creates the total ordering array with groups for element placement
def calculateTotalElementOrderArray(pregroup, groupOrder, postgroup, totalToPlace):
    numToPlace = calculateNumLeft(totalToPlace, pregroup+postgroup);
    finalOrdering = [];
    finalOrdering.extend(calculateElementOrderArray(pregroup));
    finalOrdering.extend(calculateGroupOrdering(groupOrder, numToPlace));
    finalOrdering.extend(calculateElementOrderArray(postgroup));
    return finalOrdering;

## Thresholds data
def thresholdMapData(m, THRESH):
    retMat = copy.deepcopy(m);
    for i in range(len(retMat)):
        for j in range(len(retMat[0])):
            if(abs(m[i][j]) > THRESH):
                if(m[i][j]>0):
                    retMat[i][j] = THRESH;
                else:
                    retMat[i][j] = -THRESH;
    return retMat;

## Calculates how many elements should be placed for the group
def calculateNumLeft(totalToPlace, orderPlan):
    numToPlace = totalToPlace+[];
    for order in orderPlan:
        numToPlace[order[0]] -= order[1];
    return numToPlace;

## Creates the ordering array for a specific order plan
def calculateElementOrderArray(orderPlan):
    ordering = [];
    for plan in orderPlan:
        elemType = plan[0];
        num = plan[1];
        ordering.append([lhArray[elemType][0], lhArray[elemType][1], elemType, num]);
    return ordering;

## Creates the ordering array for a group
def calculateGroupOrdering(groupOrder, numToPlace):
    driverType = groupOrder[0]
    numDriver = numToPlace[driverType];
    ordering = [];
    numPlaced = [0]*len(lhArray);
    for i in range(numDriver):
        ordering.append([lhArray[driverType][0], lhArray[driverType][1], driverType, 1]);
        for elemType in groupOrder[1:]:
            n = min(numToPlace[elemType]-numPlaced[elemType], math.ceil(numToPlace[elemType]/float(numDriver)));
            ordering.append([lhArray[elemType][0], lhArray[elemType][1], elemType, n]);
            numPlaced[elemType] += n;
    return ordering;

## Creates the ordering array for element placement
def calculateElementOrder(numLargeConfRooms, numElems):
    ordering = [];
    numPlaced = [0]*len(numElems);
    for i in range(numLargeConfRooms):
        ordering.append([lhArray[2][0], lhArray[2][1], 2, 1]);
        for elemType,numToPlace in enumerate(numElems):
            n = min(numToPlace-numPlaced[elemType], numToPlace/numLargeConfRooms+1);
            ordering.append([lhArray[elemType][0], lhArray[elemType][1], elemType, n]);
            numPlaced[elemType] += n;
    return ordering;

## Environment object
class Environment:
    def __init__(self, xlen, ylen):
        self.grid = [];
        self.xlen = xlen;
        self.ylen = ylen;
        self.elementList = {};
        for i in range(ylen):
            self.grid.append([]);
            for j in range(xlen):
                self.grid[i].append({});
    def get(self, i, j):
        return self.grid[i][j];
    def put(self, i, j, elem):
        self.grid[i][j] = elem;

## Instantiates a heat map which contains field info
class HeatMap:
    def __init__(self, env, numElements):
        self.env = env;
        self.initializeFields_(numElements);

    ## Initializes the fields (no Elements yet)
    def initializeFields_(self, numElements):
        emptyField = {};
        for i in range(numElements):
            emptyField[i] = 0;
        for y in range(self.env.ylen):
            for x in range(self.env.xlen):
                self.env.put(y,x, {
                    'field':copy.copy(emptyField),
                    'daylightfield': 0,
                    'centerfield': 0,
                    'occupied': 0,
                    'ofield': 0,
                    'adj_circ': {}});

    # Creates field values for the Elements in the field of the heat map
    def populateField(self, obs):
        for y in range(self.env.ylen):
            for x in range(self.env.xlen):
                for ob in obs:
                    fields = calculateFields(x,y,ob);
                    self.env.grid[y][x]['field'][ob.elemType] += fields[0];
                    self.env.grid[y][x]['ofield'] += fields[1];
        for yOb in range(ob.y, min(ob.y+ob.h, self.env.ylen)):
            for xOb in range(ob.x, min(ob.x+ob.l, self.env.xlen)):
                self.env.grid[yOb][xOb]['occupied'] += 1;

    # Creates the field values for circulation in the field of the heat map
    def addCirculation(self, elem):
        def addCirculationDecay(x,y,d):
            self.env.grid[y][x]['ofield'] -= CIRCULATION_MAX_VALUE/d;
        def addAdjacentCirculation(x,y,ID):
            self.env.grid[y][x]['adj_circ'][ID] = True;

        # Four sides Extension
        for y in range(elem.y+elem.h,min(elem.y+elem.h+CIRCULATION_BLOCK, self.env.ylen)):
            for x in range(self.env.xlen):
                if(not(x>=elem.x and x<elem.x+elem.l)):
                    d = abs(elem.x+0.5*elem.l-x)+1;
                    addCirculationDecay(x,y,d);
        for y in range(max(elem.y-CIRCULATION_BLOCK, 0), elem.y):
            for x in range(self.env.xlen):
                if(not(x>=elem.x and x<elem.x+elem.l)):
                    d = abs(elem.x+0.5*elem.l-x)+1;
                    addCirculationDecay(x,y,d);
        for y in range(self.env.ylen):
            for x in range(elem.x+elem.l, min(elem.x+elem.l+CIRCULATION_BLOCK, self.env.xlen)):
                if(not(y>=elem.y and y<elem.y+elem.h)):
                    d = abs(elem.y+0.5*elem.h-y)+1;
                    addCirculationDecay(x,y,d);
        for y in range(self.env.ylen):
            for x in range(max(elem.x-CIRCULATION_BLOCK, 0), elem.x):
                if(not(y>=elem.y and y<elem.y+elem.h)):
                    d = abs(elem.y+0.5*elem.h-y)+1;
                    addCirculationDecay(x,y,d);

        # Adjacent Circulation
        elem.circulationUnitsLeft = self.countCirculationUnitsLeft(elem);
        for y in range(elem.y+elem.h,min(elem.y+elem.h+CIRCULATION_BLOCK, self.env.ylen)):
            for x in range(elem.x,elem.x+elem.l):
                if(not(self.env.grid[y][x]['occupied'])):
                    addAdjacentCirculation(x,y,elem.ID);
        for y in range(max(elem.y-CIRCULATION_BLOCK, 0), elem.y):
            for x in range(elem.x,elem.x+elem.l):
                if(not(self.env.grid[y][x]['occupied'])):
                    addAdjacentCirculation(x,y,elem.ID);
        for y in range(elem.y,elem.y+elem.h):
            for x in range(elem.x+elem.l, min(elem.x+elem.l+CIRCULATION_BLOCK, self.env.xlen)):
                if(not(self.env.grid[y][x]['occupied'])):
                    addAdjacentCirculation(x,y,elem.ID);
        for y in range(elem.y,elem.y+elem.h):
            for x in range(max(elem.x-CIRCULATION_BLOCK, 0), elem.x):
                if(not(self.env.grid[y][x]['occupied'])):
                    addAdjacentCirculation(x,y,elem.ID);
        # Find Affected Elements
        affectedElemIDs = set();
        for y in range(elem.y, elem.y+elem.h):
            for x in range(elem.x, elem.x+elem.l):
                IDs = self.env.grid[y][x]['adj_circ'].keys(); 
                for ID in IDs:
                    if(self.env.grid[y][x]['adj_circ'][ID]):
                        affectedElemIDs.add(ID);
        self.updateCirculationUnits([self.env.elementList[ID] for ID in affectedElemIDs]);

    # Counts the Number of Circulation Units left around an element
    def countCirculationUnitsLeft(self, elem):
        n = elem.circulationUnits;
        for y in range(elem.y+elem.h,min(elem.y+elem.h+CIRCULATION_BLOCK, self.env.ylen)):
            for x in range(elem.x,elem.x+elem.l):
                if(self.env.grid[y][x]['occupied']):
                    n-=1;
        for y in range(max(elem.y-CIRCULATION_BLOCK, 0), elem.y):
            for x in range(elem.x,elem.x+elem.l):
                if(self.env.grid[y][x]['occupied']):
                    n-=1;
        for y in range(elem.y,elem.y+elem.h):
            for x in range(elem.x+elem.l, min(elem.x+elem.l+CIRCULATION_BLOCK, self.env.xlen)):
                if(self.env.grid[y][x]['occupied']):
                    n-=1;
        for y in range(elem.y,elem.y+elem.h):
            for x in range(max(elem.x-CIRCULATION_BLOCK, 0), elem.x):
                if(self.env.grid[y][x]['occupied']):
                    n-=1;
        return n;

    # Updates the units and powers for each element
    def updateCirculationUnits(self, elems):
        for elem in elems:
            elem.circulationUnitsLeft = self.countCirculationUnitsLeft(elem);
            for y in range(elem.y+elem.h,min(elem.y+elem.h+CIRCULATION_BLOCK, self.env.ylen)):
                for x in range(elem.x,elem.x+elem.l):
                    if(self.env.grid[y][x]['occupied']):
                        self.env.grid[y][x]['adj_circ'][elem.ID] = False;
            for y in range(max(elem.y-CIRCULATION_BLOCK, 0), elem.y):
                for x in range(elem.x,elem.x+elem.l):
                    if(self.env.grid[y][x]['occupied']):
                        self.env.grid[y][x]['adj_circ'][elem.ID] = False;
            for y in range(elem.y,elem.y+elem.h):
                for x in range(elem.x+elem.l, min(elem.x+elem.l+CIRCULATION_BLOCK, self.env.xlen)):
                    if(self.env.grid[y][x]['occupied']):
                        self.env.grid[y][x]['adj_circ'][elem.ID] = False;
            for y in range(elem.y,elem.y+elem.h):
                for x in range(max(elem.x-CIRCULATION_BLOCK, 0), elem.x):
                    if(self.env.grid[y][x]['occupied']):
                        self.env.grid[y][x]['adj_circ'][elem.ID] = False;

    # Adds the Daylight Field to the floor plate
    def addDaylightField(self, sides):
        xl = self.env.xlen;
        yl = self.env.ylen;
        for s in sides:
            if(s == 0):
                for x in range(xl):
                    for y in range(yl):
                        d = y;
                        curField = self.env.grid[y][x]['daylightfield'];
                        if(d > DAYLIGHT_INFLUENCE):
                            self.env.grid[y][x]['daylightfield'] = max(0, curField);
                        else:
                            #self.env.grid[y][x]['daylightfield'] = max(1,curField);
                            self.env.grid[y][x]['daylightfield'] = max(math.exp(-(d/float(yl)))**2, curField);
            if(s == 1):
                for x in range(xl):
                    for y in range(yl):
                        d = xl-x;
                        curField = self.env.grid[y][x]['daylightfield'];
                        if(d > DAYLIGHT_INFLUENCE):
                            self.env.grid[y][x]['daylightfield'] = max(0, curField);
                        else:
                            #self.env.grid[y][x]['daylightfield'] = max(1,curField);
                            self.env.grid[y][x]['daylightfield'] = max(math.exp(-(d/float(yl)))**2, curField);
            if(s == 2):
                for x in range(xl):
                    for y in range(yl):
                        d = yl-y;
                        curField = self.env.grid[y][x]['daylightfield'];
                        if(d > DAYLIGHT_INFLUENCE):
                            self.env.grid[y][x]['daylightfield'] = max(0, curField);
                        else:
                            #self.env.grid[y][x]['daylightfield'] = max(1,curField);
                            self.env.grid[y][x]['daylightfield'] = max(math.exp(-(d/float(xl)))**2, curField);            
            if(s == 3):
                for x in range(xl):
                    for y in range(yl):
                        d = x;
                        curField = self.env.grid[y][x]['daylightfield'];
                        if(d > DAYLIGHT_INFLUENCE):
                            self.env.grid[y][x]['daylightfield'] = max(0, curField);
                        else:
                          #self.env.grid[y][x]['daylightfield'] = max(1,curField);
                          self.env.grid[y][x]['daylightfield'] = max(math.exp(-(d/float(xl)))**2, curField);

    # Adds the center field to the floor plate
    def addCenterField(self):
        xl = self.env.xlen;
        yl = self.env.ylen;
        for y in range(yl):
            for x in range(xl):
                self.env.grid[y][x]['centerfield'] = math.exp(-(((x-0.5*xl)/xl)**2+((y-0.5*yl)/yl)**2));

    # Displays the heat map
    def show(self, scaleVector):
        m = self.returnElementsMap();
        #m = self.returnHeatMapData(scaleVector);
        plt.imshow(m, cmap = 'jet');
        plt.xticks(numrange(0, self.env.xlen, 5));
        plt.yticks(numrange(0, self.env.ylen, 5));
        plt.grid(True);
        plt.show();

    # Returns the Heat Map Data
    def returnHeatMapData(self, elemType):
        m = [];
        scaleVector = A[elemType];
        for i in range(self.env.ylen):
            m.append([]);
            for j in range(self.env.xlen):
                m[i].append(vectorProduct(self.getFieldVector(i, j), scaleVector)
                    +self.env.grid[i][j]['ofield']
                    +daylightAdj[elemType]*self.env.grid[i][j]['daylightfield']
                    +centerFieldAdj[elemType]*self.env.grid[i][j]['centerfield']
                    -self.getMaxCirculationValue(j,i));
        return m;

    ## Calculates the circulation values at a grid point
    def getMaxCirculationValue(self, x,y):
        maxVal = 0;
        for n in self.env.grid[y][x]['adj_circ'].keys():
            elem = self.env.elementList[n];
            val = elem.alpha*(1-elem.circulationUnitsLeft/float(elem.circulationUnits));
            if(val > maxVal):
                maxVal = val;
        return maxVal;

    # Returns the Heat Map with Elements
    def returnElementsMap(self):
        m = [];
        for i in range(self.env.ylen):
            m.append([]);
            for j in range(self.env.xlen):
                if(self.env.grid[i][j]['occupied']>0):
                    #m[i].append(self.env.grid[i][j]['ofield']);
                    m[i].append(self.env.grid[i][j]['occupied']);
                else:
                    m[i].append(0);
        return m;

    # Returns the field values as a list
    def getFieldVector(self, y, x):
        f = self.env.get(y,x)['field'];
        return f.values();

    # Returns the (x,y) point that maximizes a convolved map for a convolving rectangle of length l
    # and height h
    def maximizeConvolvedHeatMap(self, l, h, elemType):
        maxVal = -float('inf');
        maxInds = [-1, -1];
        m = self.returnHeatMapData(elemType);
        for x in range(self.env.xlen-l+1):
            for y in range(self.env.ylen-h+1):
                val = 0;
                for xl in range(x, min(x+l, self.env.xlen)):
                    for yl in range(y, min(y+h, self.env.ylen)):
                        val += m[yl][xl];
                if(val >= maxVal):
                    maxVal = val;
                    maxInds = [y, x];
        return [maxInds, maxVal];


## Element Object
class Element:
    def __init__(self, x, y, l, h, elemType, ID):
        self.elemType = elemType;
        self.x = x;
        self.y = y;
        self.l = l;
        self.h = h;
        self.ID = ID;
        self.THRESH = (l+h);
        self.SIZE = max(0.5*l,0.5*h);
        self.circulationUnits = CIRCULATION_BLOCK*(2*l+2*h);
        self.circulationUnitsLeft = self.circulationUnits;
        self.alpha = alphaVals[elemType]; ## Constant for now, but tunable

## Calculates the field values via a distance metric
def calculateFields(x, y, ob):
    field = 0;
    ofield = 0;
    if(outsideElement(x, y, ob)):
        d = maxdistance([x,y],[ob.x+0.5*ob.l, ob.y+0.5*ob.h]);
        if(d < ob.THRESH):
            #field = math.exp(-d/float(DECAY));
            field = min(1,1./d);
        else:
            field = 0;
    else:
        ofield = -ELEMENT_MAX_VALUE;
    return [field, ofield];

## Calculates whether a point is outside a rectangular Element
def outsideElement(x, y, ob):
    result = (x >= ob.x) and (x < ob.x+ob.l) and (y >= ob.y) and (y < ob.y+ob.h);
    return not(result);

## Infinity Norm
def maxdistance(p0, p1):
    return max(abs(p0[0]-p1[0]), abs(p0[1]-p1[1]));

## Square distance
def sqdistance(p0, p1):
    return (p0[0] - p1[0])**2 + (p0[1] - p1[1])**2;

## Vector dot Product
def vectorProduct(v1, v2):
    tot = 0;
    for i in range(len(v1)):
        tot += v1[i]*v2[i];
    return tot;

## Range (to replace np arange)
def numrange(st, end, delta):
    x = [];
    i = st;
    while (i < end):
        x.append(i);
        i += delta;
    return x;

if __name__ == '__main__':
    runScript();
    Type = objType;
    Xpos = objX;
    Ypos = objY;