from typing import List, Optional
from database import items_collection, clock_in_collection
from bson import ObjectId
from datetime import date, datetime,timezone

from schemas import ItemCreate, ItemResponse

# CRUD for Items
def create_item(item_data):
    item_data['insert_date'] = datetime.now(timezone.utc)
    if 'expiry_date' in item_data:
        item_data['expiry_date'] = datetime.combine(item_data['expiry_date'], datetime.min.time())
        result = items_collection.insert_one(item_data)
        return str(result.inserted_id)

def get_item(item_id: str):
    item =  items_collection.find_one({"_id": ObjectId(item_id)})  # Fetch from MongoDB
    return item

def update_item(item_id: str, item_data: dict):
    # Build update dictionary, excluding 'insert_date'
    update_data = {}
    
    # Convert expiry_date to datetime if provided
    if 'expiry_date' in item_data and item_data['expiry_date'] is not None:
        expiry_datetime = datetime.combine(item_data['expiry_date'], datetime.min.time())
        update_data['expiry_date'] = expiry_datetime

    # Include other fields
    for key, value in item_data.items():
        if key != 'expiry_date' and value is not None:
            update_data[key] = value

    if update_data:  # Only update if there's something to update
         items_collection.update_one({"_id": ObjectId(item_id)}, {"$set": update_data})

def delete_item(item_id):
    return items_collection.delete_one({"_id": ObjectId(item_id)})

def filter_items(email: Optional[str] = None, 
                 expiry_date: Optional[date] = None, 
                 insert_date: Optional[datetime] = None, 
                 quantity: Optional[int] = None) -> List[ItemCreate]:
    query = {}
    
    # Add filters to the query if provided
    if email:
        query['email'] = email
    
    if expiry_date:
        query['expiry_date'] = {"$gt": datetime.combine(expiry_date, datetime.min.time())}  # Ensure datetime comparison
    
    if insert_date:
        if not isinstance(insert_date, datetime):
            raise HTTPException(status_code=400, detail="insert_date must be a datetime")
        query['insert_date'] = {"$gt": insert_date}  # Ensure insert_date is a datetime
    
    if quantity is not None:  # Handle None for quantity explicitly
        query['quantity'] = {"$gte": quantity}
    
    # Fetch items from the collection
    items = list(items_collection.find(query))
    
    # Convert items to a proper format to return
    return [
        ItemCreate(
            id=str(item["_id"]),
            name=item["name"],
            email=item["email"],
            item_name=item["item_name"],
            quantity=item["quantity"],
            expiry_date=item["expiry_date"].date(),  # Convert to date for the response
            insert_date=item["insert_date"]
        )
        for item in items
    ]


def aggregate_items_by_email():
    pipeline = [{"$group": {"_id": "$email", "count": {"$sum": 1}}}]
    return list(items_collection.aggregate(pipeline))

# CRUD for Clock-In
def create_clock_in(clock_in_data):
    clock_in_data['insert_datetime'] = datetime.now(timezone.utc)
    result = clock_in_collection.insert_one(clock_in_data)
    return str(result.inserted_id)

def get_clock_in(clock_in_id):
    clock_in = clock_in_collection.find_one({"_id": ObjectId(clock_in_id)})
    if clock_in:
        # Convert MongoDB's `_id` to `id` for the response
        clock_in['id'] = str(clock_in.pop('_id'))
    return clock_in

def update_clock_in(clock_in_id, update_data):
    clock_in_collection.update_one({"_id": ObjectId(clock_in_id)}, {"$set": update_data})
    return get_clock_in(clock_in_id)

def delete_clock_in(clock_in_id):
    return clock_in_collection.delete_one({"_id": ObjectId(clock_in_id)})

def filter_clock_in(email=None, location=None, insert_datetime=None):
    query = {}
    
    # Construct the query based on provided parameters
    if email:
        query['email'] = email
    if location:
        query['location'] = location
    if insert_datetime:
        query['insert_datetime'] = {"$gt": insert_datetime}

    # Perform the query and convert results to list
    results = clock_in_collection.find(query)
    
    # Convert MongoDB documents to JSON-serializable format
    clock_in_list = []
    for record in results:
        record['_id'] = str(record['_id'])  # Convert ObjectId to string
        if 'insert_datetime' in record:
            record['insert_datetime'] = record['insert_datetime'].isoformat()  # Convert datetime to ISO format
        clock_in_list.append(record)
    
    return clock_in_list