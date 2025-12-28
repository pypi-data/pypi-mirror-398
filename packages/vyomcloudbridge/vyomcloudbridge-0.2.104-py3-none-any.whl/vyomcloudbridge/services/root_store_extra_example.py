def main():
    """Example of how to use the RootStore"""
    print("Starting general root store service example")
    from vyomcloudbridge.services.root_store import RootStore

    root_store = RootStore()

    try:
        # Example: Store user details
        unset_key_example = root_store.get_data("unset_key_example")
        print(f"Retrieved user: {unset_key_example}")

        user_data = {
            "id": 1,
            "name": "Test User",
            "email": "testuser@example.com",
            "role": "operator",
        }
        root_store.set_data("user_details", user_data)

        # Retrieve the stored data
        retrieved_user = root_store.get_data("user_details")
        print(f"Retrieved user: {retrieved_user}")

        # Update with new data
        new_user_data = {
            "id": 2,
            "name": "Another User",
            "email": "another@example.com",
            "role": "admin",
        }
        root_store.set_data("user_details", new_user_data)

        # Retrieve the updated data
        updated_user = root_store.get_data("user_details")
        print(f"Updated user: {updated_user}")

        # Delete the data
        root_store.delete_data("user_details")

        # Verify deletion
        after_delete = root_store.get_data("user_details")
        print(f"After delete: {after_delete}")

        # Try to use a reserved key (should raise ValueError)
        try:
            print(f"Try to use a reserved key (should expect ValueError).....")
            root_store.set_data("current_user", user_data)
        except ValueError as e:
            print(f"Expected error: {e}")

        # Store different types of data
        config_data = {"theme": "dark", "notifications": True, "auto_update": False}
        root_store.set_data("app_config", config_data)

        # Retrieve the config data
        retrieved_config = root_store.get_data("app_config")
        print(f"Retrieved config: {retrieved_config}")

        # Store an integer value
        root_store.set_data("temp_id", 2)
        temp_data = root_store.get_data("temp_id")
        print(f"Retrieved temp_data: {temp_data}")

        # Store a string
        root_store.set_data("message", "Hello, RabbitMQ!")
        message = root_store.get_data("message")
        print(f"Retrieved message: {message}")

        # Store a list
        root_store.set_data("colors", ["red", "green", "blue"])
        colors = root_store.get_data("colors")
        print(f"Retrieved colors: {colors}")

        location = {"lat": 76.987934, "long": 76.937954, "timestamp": "93u4983"}
        health = {"status": 1, "message": ""}
        root_store.set_data("location", location)
        root_store.set_data("health", health)
    except Exception as e:
        print("Error occured -", {str(e)})
    finally:
        root_store.cleanup()


if __name__ == "__main__":
    main()
