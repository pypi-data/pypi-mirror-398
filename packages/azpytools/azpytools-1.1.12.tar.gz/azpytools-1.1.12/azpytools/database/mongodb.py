import pymongo
 
class MongoDb():
    
    def __init__(self,url,dbname) -> None:
        dbhost = f"mongodb://{url}/" #"mongodb://localhost:27017/"
        self.client =  pymongo.MongoClient(dbhost)
        self.Database = self.client[dbname]
    
    def getDatabaseList(self):
        dblist = self.client.list_database_names()
        return dblist
        

    def setDatabaseName(self,dbname):
        self.Database = self.client[dbname]
        
    def getCollection(self):
        collist = self.Database.list_collection_names()
        return collist

    
    def createCollection(self,tableName):
        mycol = self.Database[tableName]
    
    def inserRecord(self,tableName,document):
        curCollection = self.Database[tableName]
        insertDict = document
        result =  curCollection.insert_one(insertDict)
        # return result.inserted_id
        
    def inserRecords(self,tableName,documents):
        curCollection = self.Database[tableName]
        insertDictList = documents
        result =  curCollection.insert_many(insertDictList)
        # return result.inserted_ids
        
    def getRecordsAll(self,tableName,condDict:dict):
        curCollection = self.Database[tableName]
        resultDocs = list(curCollection.find(condDict))
        return resultDocs
    
    def inserRecordBeforeCheck(self,tableName,document,keyField,keyValue ):
        lresult = None
        cond = {keyField:keyValue}
        lresult = self.getRecordsAll(tableName,cond)
        if  lresult == [] or lresult == None:
            self.inserRecord(tableName,document)
    
    def close(self):
        self.client.close()
    