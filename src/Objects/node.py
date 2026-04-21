class Node:
    def __init__(self, id, lat, lng, name = None):
        self.id = id
        self.lat = lat
        self.lng = lng
        self.name = name
    
    def getID(self):
        return self.id
    
    def getLat(self):
        return self.lat
    
    def getLng(self):
        return self.lng
    
    def getName(self):
        return self.name