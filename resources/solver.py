"""
This code solves the problem based on a need vs availability.

Ranking is based on distance of cities (takers) from resources.

As far as I remember the algorithm was ranking all the points in the first round and then each city
starts taking the closest resources in each round until there is nothing left!

args:
    pxPts: I assume each branch contains points for a specific landuse type
    takers: List of points for settelments location
    forest: List of integers that shows the need for forest for each taker
    natural: similar to forest
    agriculture: similar to forest
    wetlands: similar to forest
    water: similar to forest
    developed: similar to forest
"""

import Rhino as rc
import scriptcontext as sc
import Grasshopper.Kernel as gh
from System import Object
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path

class sourcePx(object):
    def __init__(self, id, location):
        self.id = id
        self.location = location
        self.distanceTo = {}
        self.isTaken = False
        self.takerRank = {}
        
    def rankTakers(self, takersCollection):
        sortedTakers = sorted(takersCollection,  key=lambda tk: tk.distanceTo[self.id])
        
        for count, tk in enumerate(sortedTakers):
            self.takerRank[tk.id] = count 
        
class taker(object):
    
    def __init__(self, id, location, needs):
        self.id = id
        self.location = location
        self.distanceTo = {}
        self.sortedPx = {}
        self.need = []
        for n in needs: self.need.append(n[id])
        self.takenCount = {}
        self.isSatisfied = {}
        for landuse in range(len(self.need)):
            self.takenCount[landuse] = 0
            self.isSatisfied[landuse] = False
        
        self.taken = {
                       "roundI" : [],
                       "roundII" : [],
                       "roundIII" : []
                      }
        # create empty lists for each need for each round
        for round in self.taken.keys():
            for landuse in range(len(self.need)):
                self.taken[round].append([])
                
    def getDistanceTo(self, px):
        distance = px.location.DistanceTo(self.location)
        px.distanceTo[self.id] = distance
        self.distanceTo[px.id] = distance
    
    def sortPxBasedOnDist(self, landuse, pxCollection):
        # find distance
        for px in pxCollection:
            self.getDistanceTo(px)
        
        # sort px based on distance
        self.sortedPx[landuse] = sorted(pxCollection,  key=lambda px: px.distanceTo[self.id])
        

def main(pxPts, takers, need):
    """
    pixels as a list of points
    takers as list of points
    need as an integer
    """
    
    takersCollection = []
    # create an object for every taker
    for id, tPt in enumerate(takers):
        tk = taker(id, tPt, need) 
        takersCollection.append(tk)
    
    pxCollection = {}
    
    for landuse in range(len(need)):
        pixels = pxPts.Branch(landuse)
        pxCollectForEachLandUse = []
        # create an object for each px and find distance to takers
        for id, pt in enumerate(pixels):
            px = sourcePx(id, pt)
            pxCollectForEachLandUse.append(px)
            
        pxCollection[landuse] = pxCollectForEachLandUse
    
    # rank all the takers 
    for landuse in pxCollection.keys():
        # each taker rank the pixels based on distance
        for tk in takersCollection:
            tk.sortPxBasedOnDist(landuse, pxCollection[landuse])
    
        # let each pixel also rank the takers based on distance
        for px in pxCollection[landuse]:
            px.rankTakers(takersCollection)
    
    # now that everything is ranked let's see who can take whome
    satisfied = []
    for landuse in range(len(need)): satisfied.append(0) 
    
    # round I - each taker will try to take as much as it needs from pixels
    # with similar land use
    for landuse in range(len(need)):
        for rank in range(len(takers)):
            if satisfied[landuse] >= len(takers):
                break
            else:
                for tk in takersCollection:
                    for px in tk.sortedPx[landuse]:
                        if tk.takenCount[landuse] >= tk.need[landuse]:
                            tk.isSatisfied[landuse] = True
                            satisfied[landuse] += 1 # one of the takers is satisfied
                            break
                        else:
                            # check if taker is eligible to take this px
                            if not px.isTaken and px.takerRank[tk.id] == rank:
                                # take it
                                tk.taken["roundI"][landuse].append(px)
                                tk.takenCount[landuse] += 1
                                px.isTaken = True
    
    # assert False
    # round II and III
    # round II: if still needs agriculture, take it from nature and from forest
    # round III: if still needs forest, take it from nature and from agriculture
    
    # this part of the code is not well written!
    LUs = {0 : "Forest",
           1 : "Natural",
           2 : "Agriculture"
           }
    alternateSourceLandUses = [[1,0], [1,2]]
    landuseNeeded = [2, 0]
    rounds = ["roundII", "roundIII"]
    
    for roundCount, round in enumerate(rounds):
        print round
        for alternateSource in alternateSourceLandUses[roundCount]:
            for rank in range(len(takers)):
                for tk in takersCollection:
                    #print "time for : " + LUs[landuseNeeded[roundCount]] + " for taker " + `tk.id`
                    # print tk.id, ":", tk.isSatisfied[landuseNeeded[roundCount]]
                    if not tk.isSatisfied[landuseNeeded[roundCount]]:
                        print "Looking for more " + LUs[landuseNeeded[roundCount]] + " in " + LUs[alternateSource]
                        for px in tk.sortedPx[alternateSource]:
                            if tk.takenCount[landuseNeeded[roundCount]] >= tk.need[landuseNeeded[roundCount]]:
                                tk.isSatisfied[landuseNeeded[roundCount]] = True
                                satisfied[landuseNeeded[roundCount]] += 1 # one of the takers is satisfied
                                print "found enough for " + LUs[landuseNeeded[roundCount]] + " for taker " + `tk.id`
                                break
                            else:
                                # check if taker is eligible to take this px
                                # print round + " taking from " + LUs[alternateSource] + " for " + LUs[landuseNeeded[roundCount]] 
                                if not px.isTaken and px.takerRank[tk.id] == rank:
                                    # take it
                                    tk.taken[round][alternateSource].append(px)
                                    tk.takenCount[landuseNeeded[roundCount]] += 1
                                    px.isTaken = True
                    else:
                        "taker " + `tk.id` + "is already satidfied for " + LUs[landuseNeeded[roundCount]]
    return takersCollection
    
i = DataTree[Object]()
i_I = DataTree[Object]()
i_II = DataTree[Object]()

needs = [forest, natural, agriculture, wetlands, water, developed]

takersCollection = main(pxPts, takers, needs)


for tk in takersCollection:
    for landUseId, landUsePxs in enumerate(tk.taken["roundI"]):
        p = GH_Path(tk.id, landUseId)
        pxIds = []
        for px in landUsePxs: pxIds.append(px.id)
        i.AddRange(pxIds, p)
    for landUseId, landUsePxs in enumerate(tk.taken["roundII"]):
        p = GH_Path(tk.id, landUseId)
        pxIds = []
        for px in landUsePxs: pxIds.append(px.id)
        i_I.AddRange(pxIds, p)
    for landUseId, landUsePxs in enumerate(tk.taken["roundIII"]):
        p = GH_Path(tk.id, landUseId)
        pxIds = []
        for px in landUsePxs: pxIds.append(px.id)
        i_II.AddRange(pxIds, p)
    
    
    
    # for each land use append the items index
    
#for takerID, itemList in itemsDict.items():
#    p = GH_Path(takerID, branchCount)
#    i.AddRange(itemList[0], p)
#    i_I.AddRange(itemList[1], p)
#    i_II.AddRange(itemList[2], p)