from typing import Tuple
import time

def _check_rate(sub_tracker: dict, rate: float, now: float) -> Tuple[bool, float]:
    """Helper to check throttling for a specific rate."""
    if rate <= 0:
        return False, 0.0

    min_interval = 1.0 / rate
    last_print_time = sub_tracker.get("last_print_time")

    if last_print_time is None or (now - last_print_time) >= min_interval:
        dt = now - last_print_time if last_print_time else 0
        freq = 1.0 / dt if dt > 0 else 0.0
        sub_tracker["last_print_time"] = now
        return True, freq

    return False, 0.0

def should_throttle(
    tracker: dict,
    destination: str,
    live_rate: float,
    buffered_rate: float,
    now: float = None
) -> Tuple[bool, bool, float, float, bool]:
    """
    Determines whether a message should be sent live or buffered based on throttling intervals.

    Parameters:
        tracker (dict): Stores timings and frequencies per destination/mode.
        destination (str): e.g. 'gcs', 'local'.
        live_rate (float): Max allowed live send rate (Hz).
        buffered_rate (float): Max allowed buffered send rate (Hz).
        now (float): Current timestamp (sec).

    Returns:
        save_locally_or_send (bool): Whether to send buffered data (False) or save locally (True).
        send_live (bool): Whether to send live data.
        upload_freq (float): Buffered upload frequency (Hz).
        msg_freq (float): Message arrival frequency (Hz).
        is_local_save (bool): True if destination == "local".
    """
    # Ensure tracker structure exists for this destination
    if destination not in tracker:
        tracker[destination] = {"live": {}, "buffered": {}, "last_time": None}

    dest_tracker = tracker[destination]

    # --- Common message frequency ---
    last_time = dest_tracker.get("last_time")
    if last_time is not None:
        dt = now - last_time
        msg_freq = 1.0 / dt if dt > 0 else 0.0
    else:
        msg_freq = 0.0
    dest_tracker["last_time"] = now

    # --- Buffered throttling ---
    buffered_tracker = dest_tracker["buffered"]
    can_send_buffered, buffered_freq = _check_rate(buffered_tracker, buffered_rate, now)
    
    if (destination.lower() == "local") and can_send_buffered:
        return True, False, buffered_freq, 0, msg_freq, True

    # --- Live throttling ---
    live_tracker = dest_tracker["live"]
    can_send_live, live_freq = _check_rate(live_tracker, live_rate, now)
        
    return can_send_buffered, can_send_live, buffered_freq, live_freq, msg_freq, False



