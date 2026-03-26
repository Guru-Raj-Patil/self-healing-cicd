from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client['cicd_healing']

def init_db():
    pass

def save_analysis(job_name, build_number, workspace, error_type, confidence, keywords, explanation, recommended_fix):
    collection = db['analysis']
    record = {
        "job_name": job_name,
        "build_number": build_number,
        "workspace": workspace,
        "error_type": error_type,
        "confidence": confidence,
        "keywords": keywords,
        "explanation": explanation,
        "recommended_fix": recommended_fix,
        "status": "pending_fix"
    }
    res = collection.insert_one(record)
    return res.inserted_id

def update_status(record_id, status, fix_output=""):
    from bson.objectid import ObjectId
    collection = db['analysis']
    collection.update_one(
        {"_id": ObjectId(record_id)},
        {"$set": {"status": status, "fix_output": fix_output}}
    )

def get_history():
    collection = db['analysis']
    records = list(collection.find().sort('_id', -1).limit(50))
    for r in records:
        r['_id'] = str(r['_id'])
    return records
