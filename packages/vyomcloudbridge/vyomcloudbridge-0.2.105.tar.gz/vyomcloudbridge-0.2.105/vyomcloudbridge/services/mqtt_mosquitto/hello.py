import signal
import sys
import time

def main():
    is_running = True

    def signal_handler(sig, frame):
        nonlocal is_running
        print(f"Received signal {sig}, shutting down...")
        is_running = False
        # Optionally, call cleanup functions here
        sys.exit(0)  # Ensures immediate exit after cleanup

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Listening for messages... Press Ctrl+C to exit")
    while is_running:
        time.sleep(1)  # Use a short sleep for responsiveness

    print("Exited cleanly.")

if __name__ == "__main__":
    main()