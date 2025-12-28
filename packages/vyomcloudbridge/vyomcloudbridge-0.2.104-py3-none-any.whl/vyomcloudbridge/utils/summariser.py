from statistics import mean
from typing import Any, Dict, List, Type
import math
from vyom_utils.summariser_config import CONFIG

# ============================ DEFAULT SUMMARISER ============================


class DefaultSummariser:
    def __init__(self, topic: str, unit: str):
        self.topic = topic
        self.unit = unit
        self.field_values: Dict[str, List[float]] = {}

    def update(self, topic_name: str, msg: Any):
        numeric_fields = self._flatten_numeric_fields(msg)
        self.unit = topic_name
        print(f"updating in default {msg} for name {topic_name}")
        for field_path, value in numeric_fields.items():
            if field_path.startswith("header.stamp."):
                continue
            self.field_values.setdefault(field_path, []).append(value)

    def _flatten_numeric_fields(self, msg: Any, prefix: str = "") -> Dict[str, float]:
        fields = {}
        if isinstance(msg, (int, float)):
            cleaned_key = (
                prefix.rstrip(".").lstrip("_").replace("._", ".").replace("_", ".")
            )
            fields[cleaned_key] = msg
        elif hasattr(msg, "__slots__"):
            for slot in msg.__slots__:
                value = getattr(msg, slot, None)
                slot_cleaned = slot.lstrip("_")
                full_key = f"{prefix}{slot_cleaned}"
                fields.update(self._flatten_numeric_fields(value, full_key + "."))
        return fields

    def get_summary(self) -> Dict:
        field_summary = {}
        for field, values in self.field_values.items():
            if values:
                field_summary[field] = {
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "avg": round(mean(values), 2),
                    "count": len(values),
                }
        return {"topic": self.topic, "fields": field_summary, "unit": self.unit}

    def reset(self):
        self.field_values.clear()


# ============================ VELOCITY SUMMARISER ============================


class VelocitySummariser(DefaultSummariser):
    def __init__(self, topic: str):
        super().__init__(topic, unit="meters/sec and radians/sec")

    def update(self, topic_name: str, msg: Any):
        print(f"updating in velo {msg} for name {topic_name}")
        if topic_name != self.topic:
            return
        try:
            vx = msg.twist.linear.x
            vy = msg.twist.linear.y
            vz = msg.twist.linear.z
            roll = msg.twist.angular.x
            pitch = msg.twist.angular.y
            yaw = msg.twist.angular.z

            self.field_values.setdefault("horizontal.velocity", []).append(
                math.sqrt(vx**2 + vy**2)
            )
            self.field_values.setdefault("vertical.velocity", []).append(vz)
            self.field_values.setdefault("roll", []).append(roll)
            self.field_values.setdefault("pitch", []).append(pitch)
            self.field_values.setdefault("yaw", []).append(yaw)
        except AttributeError:
            pass


# ============================ ALTITUDE SUMMARISER ============================


class AltitudeSummariser(DefaultSummariser):
    def __init__(self, topic: str):
        super().__init__(topic, unit="meters")

    def update(self, topic_name: str, msg: Any):
        print(f"updating in alti {msg} for name {topic_name}")
        if hasattr(msg, "data"):
            self.field_values.setdefault("altitude", []).append(msg.data)


# ============================ BATTERY SUMMARISER ============================


class BatterySummariser(DefaultSummariser):
    def __init__(self, topic: str):
        super().__init__(topic, unit="V, percent, A")
        self.percentage_values: List[float] = []

    def update(self, topic_name: str, msg: Any):
        print(f"updating in bat {msg} for name {topic_name}")
        try:
            self.field_values.setdefault("voltage", []).append(msg.voltage)
            self.field_values.setdefault("current", []).append(msg.current)
            self.percentage_values.append(msg.percentage)
        except AttributeError:
            pass

    def get_summary(self) -> Dict:
        summary = super().get_summary()
        if self.percentage_values:
            summary["fields"]["percentage"] = {
                "min": round(min(self.percentage_values), 2),
                "max": round(max(self.percentage_values), 2),
            }
        return summary

    def reset(self):
        super().reset()
        self.percentage_values.clear()


# ============================ SELECTOR ============================


class SummariserSelector:
    def __init__(self):
        self.is_mission = 1
        self.summarisers = []
        print("in summary")
        self.reset()
        
        

        type_to_class: Dict[str, Type[DefaultSummariser]] = {
            "geometry_msgs/msg/TwistStamped": VelocitySummariser,
            "std_msgs/msg/Float64": AltitudeSummariser,
            "sensor_msgs/msg/BatteryState": BatterySummariser,
        }

        for entry in CONFIG:
            topic = entry["topic"]
            type_str = entry["type"]

            summariser_cls = type_to_class.get(type_str, DefaultSummariser)

            if summariser_cls is DefaultSummariser:
                summariser = summariser_cls(topic, unit=type_str)
            else:
                summariser = summariser_cls(topic)

            self.summarisers.append(summariser)
            self.message_handlers[topic] = summariser.update
            
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

    def is_topic_allowed(self, topic_name: str) -> bool:
        return topic_name in self.message_handlers

    def update(self, topic_name: str, msg: Any):
        handler = self.message_handlers.get(topic_name)
        if handler:
            handler(topic_name, msg)

    def get_summary(self) -> List[Dict]:
        print("Getting summary from summariser selector")
        return [s.get_summary() for s in self.summarisers]

    def reset(self):
        for s in self.summarisers:
            s.reset()
        self.summarisers = []
        self.message_handlers = {}
        type_to_class: Dict[str, Type[DefaultSummariser]] = {
            "geometry_msgs/msg/TwistStamped": VelocitySummariser,
            "std_msgs/msg/Float64": AltitudeSummariser,
            "sensor_msgs/msg/BatteryState": BatterySummariser,
        }
        for entry in CONFIG:
            topic = entry["topic"]
            type_str = entry["type"]

            summariser_cls = type_to_class.get(type_str, DefaultSummariser)

            if summariser_cls is DefaultSummariser:
                summariser = summariser_cls(topic, unit=type_str)
            else:
                summariser = summariser_cls(topic)

            self.summarisers.append(summariser)
            self.message_handlers[topic] = summariser.update


# ============================ TEST HOOK ============================

if __name__ == "__main__":
    selector = SummariserSelector()
    print(selector.get_summary())
