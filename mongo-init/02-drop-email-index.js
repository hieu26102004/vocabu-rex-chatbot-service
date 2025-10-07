// Drop the email index if it exists (migration script)
use('vocabu_rex_chatbot');

try {
    db.users.dropIndex({ "email": 1 });
    print("Email index dropped successfully");
} catch (e) {
    print("Email index not found or already dropped: " + e.message);
}

// Also remove email field from existing users if any
try {
    db.users.updateMany(
        {},
        { $unset: { "email": "", "username": "", "preferences": "" } }
    );
    print("Removed email, username, and preferences fields from existing users");
} catch (e) {
    print("Error updating existing users: " + e.message);
}