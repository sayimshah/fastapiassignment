from pymongo import MongoClient
from urllib.parse import quote_plus

username = quote_plus("sayimshah99")
password = quote_plus("ZdPCTI1a8OI4PmZU")

client = MongoClient('mongodb+srv://sayimshah99:ZdPCTI1a8OI4PmZU@cluster0.sigwt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['fastApiAssignment']

items_collection = db['items']
clock_in_collection = db['clock_in_records']

print(items_collection)
