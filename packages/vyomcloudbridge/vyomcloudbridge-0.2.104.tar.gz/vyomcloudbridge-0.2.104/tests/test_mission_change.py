# mission_start_example.py

import sys
import signal
import threading

from vyomcloudbridge.services.mission_stats import MissionStats


def setup_signal_handlers(obj):
    """Setup signal handlers for graceful shutdown (must be called from main thread)."""
    if threading.current_thread() is not threading.main_thread():
        print("Signal handlers must be set in the main thread. Skipping setup.")
        return

    def signal_handler(sig, frame):
        print(f"\nReceived signal {sig}. Shutting down {obj.__class__.__name__}...")
        obj.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def prompt_user_action():
    """Prompt the user to either start or end a mission."""
    while True:
        action = input("\nType 'start' to begin a new mission or 'end' to end the current mission: ").strip().lower()
        if action in ['start', 'end']:
            return action
        else:
            print("Invalid input. Please type 'start' or 'end'.")


def prompt_mission_id():
    """Prompt the user for a numeric mission ID."""
    while True:
        mission_id_input = input("Enter Mission ID (must be a number): ").strip()
        if mission_id_input.isdigit():
            return int(mission_id_input)
        else:
            print("Invalid Mission ID. Please enter a numeric value.")


def wait_for_end_command():
    """Wait for the user to type 'end' to end the mission."""
    while True:
        cmd = input("\nMission is running. Type 'end' to end the mission: ").strip().lower()
        if cmd == "end":
            return
        else:
            print("Invalid input. Please type 'end'.")


def prompt_exit_or_continue():
    """Ask the user whether to exit or go back to the main menu."""
    while True:
        cmd = input("\nType 'exit' to quit or 'menu' to return to the main menu: ").strip().lower()
        if cmd in ["exit", "menu"]:
            return cmd
        else:
            print("Invalid input. Please type 'exit' or 'menu'.")


def main():
    mission_stats = MissionStats()
    setup_signal_handlers(mission_stats)

    while True:
        action = prompt_user_action()

        if action == "end":
            success, error = mission_stats.end_current_mission()
            if error:
                print("Failed to end current mission:", error)
            else:
                print("Current mission ended successfully.")
        elif action == "start":
            mission_id = prompt_mission_id()

            # End any current mission first
            success, error = mission_stats.end_current_mission()
            if error:
                print("Warning: Could not end previous mission:", error)

            mission_detail, error = mission_stats.start_mission(
                name="optional_human_readable_name",
                description="Description of mission",
            )

            if error:
                print("Failed to start mission:", error)
            else:
                print("Mission started successfully:", mission_detail)

            # Wait for user to end the mission manually
            wait_for_end_command()

            # End the mission
            success, error = mission_stats.end_current_mission()
            if error:
                print("Failed to end current mission:", error)
            else:
                print("Mission ended successfully.")

        # Ask user whether to exit or go back to the main menu
        next_step = prompt_exit_or_continue()
        if next_step == "exit":
            print("Exiting program.")
            break


if __name__ == "__main__":
    main()
