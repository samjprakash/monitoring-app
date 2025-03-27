from app import app, db, User

# Use the Flask app instance to create the application context
with app.app_context():
    # Query all users
    users = User.query.all()

    # Print the schema (columns)
    print("Schema (Columns):")
    print(User.__table__.columns.keys())
    print("\nData (Users):")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}, Created At: {user.created_at}")
