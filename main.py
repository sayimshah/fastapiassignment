from typing import List
from fastapi import FastAPI, HTTPException
from utils import *
from schemas import *
from bson.errors import InvalidId
app = FastAPI()

# Item APIs
@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    item_data = item.dict()

    # Convert expiry_date from date to datetime (midnight of that day)
    if 'expiry_date' in item_data:
        item_data['expiry_date'] = datetime.combine(item_data['expiry_date'], datetime.min.time())

    # Set insert_date to the current UTC time
    item_data['insert_date'] = datetime.now()

    # Insert into the database
    result =  items_collection.insert_one(item_data)

    # Fetch the newly created item
    created_item =  items_collection.find_one({"_id": result.inserted_id})

    if created_item:
        # Create an ID field for the response
        created_item['id'] = str(created_item.pop('_id'))  # Convert ObjectId to string
        return ItemResponse(**created_item)  # Return response model
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item_endpoint(item_id: str):
    item = get_item(item_id)
    if item:
        # Convert the ObjectId to string for the response
        item_response = ItemResponse(
            id=str(item['_id']),
            name=item['name'],
            email=item['email'],
            item_name=item['item_name'],
            quantity=item['quantity'],
            expiry_date=item['expiry_date'],
            insert_date=item['insert_date']
        )
        return item_response
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item_endpoint(item_id: str, item: ItemCreate):
    update_item(item_id, item.dict())
    updated_item =  items_collection.find_one({"_id": ObjectId(item_id)})
    if updated_item:
        return ItemResponse(
            id=str(updated_item['_id']),
            name=updated_item.get('name', None),
            email=updated_item.get('email', None),
            item_name=updated_item.get('item_name', None),
            quantity=updated_item.get('quantity', None),
            expiry_date=updated_item.get('expiry_date', None),
            insert_date=updated_item['insert_date']  # Retain the original insert_date
        )
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
def delete_item_endpoint(item_id: str):
    result = delete_item(item_id)
    if result.deleted_count:
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/items/filter/", response_model=List[ItemResponse])
def filter_items(email: Optional[str] = None, 
                        expiry_date: Optional[date] = None, 
                        quantity: Optional[int] = None):
    query = {}
    if email:
        query['email'] = email
    if expiry_date:
        query['expiry_date'] = {"$gt": expiry_date}
    if quantity is not None:
        query['quantity'] = {"$gte": quantity}

    items =  items_collection.find(query).to_list(length=None)  # Fetch filtered items
    # Convert to ItemResponse format
    for item in items:
        item['id'] = str(item['_id'])  # Convert ObjectId to string
    return [ItemResponse(**item) for item in items]

@app.get("/items/aggregate/")
def aggregate_items_by_email_endpoint():
    return aggregate_items_by_email()

# Clock-In APIs
@app.post("/clock-in", response_model=ClockInResponse)
def create_clock_in_endpoint(clock_in: ClockInCreate):
    clock_in_id = create_clock_in(clock_in.dict())
    return get_clock_in(clock_in_id)

@app.get("/clock-in/{clock_in_id}", response_model=ClockInResponse)
def get_clock_in_endpoint(clock_in_id: str):
    record = get_clock_in(clock_in_id)
    if record:
        return record
    raise HTTPException(status_code=404, detail="Clock-in record not found")

@app.put("/clock-in/{clock_in_id}", response_model=ClockInResponse)
def update_clock_in_endpoint(clock_in_id: str, clock_in: ClockInCreate):
    return update_clock_in(clock_in_id, clock_in.dict())

@app.delete("/clock-in/{clock_in_id}")
def delete_clock_in_endpoint(clock_in_id: str):
    try:
        valid_id = ObjectId(clock_in_id)  
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid Clock-in ID format")

    existing_item = clock_in_collection.find_one({"_id": valid_id})
    if not existing_item:
        print(f"No document found with ID: {valid_id}")
        raise HTTPException(status_code=404, detail="Clock-in record not found")
    
    result = delete_clock_in(valid_id)
    
    if result.deleted_count:
        return {"status": "deleted"}
    
    raise HTTPException(status_code=404, detail="Clock-in record not found")

@app.get("/clock-in/filter/")
def filter_clock_in_endpoint(email: Optional[str] = None, location: Optional[str] = None,
                             insert_datetime: Optional[datetime] = None):
    return filter_clock_in(email, location, insert_datetime)
