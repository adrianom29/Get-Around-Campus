class Edge:
    def __init__(self, start, dest, weight):
        self.start = start
        self.dest = dest
        self.weight = weight
    
    def getStart(self):
        return self.start
    
    def getDest(self):
        return self.dest
    
    def getWeight(self):
        return self.weight
    
