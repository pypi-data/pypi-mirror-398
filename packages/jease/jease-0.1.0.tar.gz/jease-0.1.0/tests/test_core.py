from jease import JEase

data = {
    "users": [
        {"name": "Alice", "age": 25, "location": {"city": "NY", "zip": 10001}},
        {"name": "Bob", "age": 30},
        {"name": "Charlie", "age": 35, "location": {"city": "LA"}}
    ]
}

JEase(data).get("users") \
    .filter(age__gte=25) \
    .sort("age") \
    .pluck("location.city", default="Unknown") \
    .unique() \
    .show()

# Update nested value
JEase(data).update("users.1.location.city", "Chicago").show()

# Remove a key
JEase(data).remove("users.0.location.zip").show()

# Merge another JSON
JEase(data).merge({"users":[{"name":"Dave","age":40}]}).show()

# Quick report
JEase(data).get("users").report()
