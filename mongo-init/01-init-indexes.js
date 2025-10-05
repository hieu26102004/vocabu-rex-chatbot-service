// MongoDB initialization script
// This script runs when MongoDB container starts for the first time

// Switch to the chatbot database
use('vocabu_rex_chatbot');

// Create indexes for better performance
db.users.createIndex({ "user_id": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true, sparse: true });

db.chat_conversations.createIndex({ "conversation_id": 1 }, { unique: true });
db.chat_conversations.createIndex({ "user_id": 1 });
db.chat_conversations.createIndex({ "created_at": -1 });

db.chat_messages.createIndex({ "conversation_id": 1 });
db.chat_messages.createIndex({ "user_id": 1 });
db.chat_messages.createIndex({ "timestamp": -1 });
db.chat_messages.createIndex({ "conversation_id": 1, "timestamp": 1 });

print("MongoDB indexes created successfully for VocabuRex Chatbot Service");