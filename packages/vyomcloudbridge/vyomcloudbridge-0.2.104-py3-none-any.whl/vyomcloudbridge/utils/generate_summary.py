import json
import os
from collections import defaultdict
from vyomcloudbridge.utils.logger_setup import setup_logger


class Summariser:
    def __init__(self, filter_file_path="filter.json", log_level=None):
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )
        self.reset()
        self.is_mission = 1

    def set_mission_mode(self, is_mission: int):
        """
        Set the mission mode for the summariser.
        :param is_mission: 0 for non-mission, 1 for mission, 2 for mission with additional fields.
        """
        self.is_mission = is_mission

    def get_mission_mode(self):
        """
        Get the current mission mode for the summariser.
        :return: The current mission mode (0, 1, or 2).
        """
        return self.is_mission

    def reset(self):
        """
        Reset the statistics and allowed fields.
        """
        self.stats = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "min": float("inf"),
                    "max": float("-inf"),
                    "sum": 0.0,
                    "count": 0,
                }
            )
        )
        self.allowed_fields = {}
        self.load_filter_from_file()

    def load_filter_from_file(self):
        """
        Load allowed topic and field filters from a JSON file.
        """
        abs_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../utils/filter_data_fields.py")
        )
        self.logger.debug(f"Looking for filter file at: {abs_path}")
        try:
            with open(abs_path, "r") as f:
                data = json.load(f)
                self.allowed_fields = {
                    topic: set(fields) for topic, fields in data.items()
                }
                self.logger.debug(
                    f"Loaded filter for topics: {list(self.allowed_fields.keys())}"
                )
        except Exception as e:
            self.logger.debug(f"Failed to load filter JSON: {e}")
            self.allowed_fields = {}

    def update(self, topic_name: str, msg):
        """
        Call this in your ROS 2 subscription callback to update stats,
        filtered by topics and fields specified in the JSON file.
        """
        self.logger.debug(f"topic_name {topic_name} came")
        if topic_name not in self.allowed_fields:
            return

        self.logger.debug(f"✅ Yes topic_name {topic_name} inside")
        allowed = self.allowed_fields[topic_name]
        numeric_fields = self.extract_numeric_fields("", msg)
        self.logger.debug(f"allowed {allowed}\nnumeric_fields {numeric_fields.keys()}")

        for field_name, value in numeric_fields.items():
            # self.logger.debug(f"allowed {allowed}\nfield_name {field_name}")
            if field_name not in allowed:
                continue
            stat = self.stats[topic_name][field_name]
            stat["min"] = min(stat["min"], value)
            stat["max"] = max(stat["max"], value)
            stat["sum"] += value
            stat["count"] += 1

    def extract_numeric_fields(self, prefix, msg):
        """
        Recursively extract numeric fields from a ROS 2 message.
        """
        fields = {}
        if hasattr(msg, "__slots__"):
            for field_name in msg.__slots__:
                value = getattr(msg, field_name, None)
                full_key = f"{prefix}.{field_name}" if prefix else field_name

                if isinstance(value, (int, float)):
                    fields[full_key] = value
                elif hasattr(value, "__slots__"):
                    fields.update(self.extract_numeric_fields(full_key, value))
                elif (
                    isinstance(value, (list, tuple))
                    and value
                    and isinstance(value[0], (int, float))
                ):
                    for i, v in enumerate(value):
                        fields[f"{full_key}[{i}]"] = v
        elif isinstance(msg, (int, float)):
            fields[prefix] = msg

        return fields

    def generate_summary(self):
        """
        Returns a summary dictionary for each topic and field, with leading underscores removed from field names.
        """
        self.logger.debug(f"Stats {self.stats}")
        summary = {}
        for topic, fields in self.stats.items():
            summary[topic] = {}
            for field, stat in fields.items():
                cleaned_field = field.lstrip("_")  # Remove leading underscore
                avg = stat["sum"] / stat["count"] if stat["count"] > 0 else None
                summary[topic][cleaned_field] = {
                    "min": stat["min"],
                    "max": stat["max"],
                    "avg": avg,
                    "count": stat["count"],
                }
        return summary

    def print_summary(self, logger=None):
        """
        Optionally logs or prints the summary to console or via a ROS 2 logger.
        """
        summary = self.generate_summary()

        self.logger.info(f"Summary details: {summary}")

        if not summary or all(not fields for fields in summary.values()):
            self.logger.debug(
                "📭 No summary data available. No matching updates received."
            )
            return

        for topic, fields in summary.items():
            out = f"📊 Summary for topic: {topic}"
            if logger:
                logger.info(out)
            else:
                self.logger.debug(out)

            for field, stats in fields.items():
                if stats["avg"] is not None:
                    line = (
                        f"  {field}: "
                        f"min={stats['min']:.3f}, "
                        f"max={stats['max']:.3f}, "
                        f"avg={stats['avg']:.3f}, "
                        f"count={stats['count']}"
                    )
                else:
                    line = f"  {field}: No valid data"

                if logger:
                    logger.info(line)
                else:
                    self.logger.debug(line)

        return summary
