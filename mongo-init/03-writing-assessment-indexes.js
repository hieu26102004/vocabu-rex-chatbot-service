// MongoDB indexes for writing assessment collection

// Create collection and indexes for writing assessments
db.writing_assessments.createIndex(
    { "submission.user_id": 1 },
    { name: "user_id_index" }
);

db.writing_assessments.createIndex(
    { "created_at": -1 },
    { name: "created_at_desc_index" }
);

db.writing_assessments.createIndex(
    { "status": 1 },
    { name: "status_index" }
);

db.writing_assessments.createIndex(
    { "submission.user_id": 1, "created_at": -1 },
    { name: "user_created_compound_index" }
);

db.writing_assessments.createIndex(
    { "submission.user_id": 1, "status": 1 },
    { name: "user_status_compound_index" }
);

db.writing_assessments.createIndex(
    { "result.overall_score": 1 },
    { 
        name: "score_index",
        partialFilterExpression: { "result": { $exists: true } }
    }
);

// Create TTL index to auto-delete old assessments after 1 year (optional)
db.writing_assessments.createIndex(
    { "created_at": 1 },
    { 
        name: "ttl_index",
        expireAfterSeconds: 31536000  // 1 year in seconds
    }
);

print("Writing assessment indexes created successfully");