from vyomcloudbridge.services.queue_worker import QueueWorker
from vyomcloudbridge.services.dir_watcher import DirWatcher
from vyomcloudbridge.services.mission_stats import MissionStats
from vyomcloudbridge.services.machine_stats import MachineStats
from vyomcloudbridge.services.stream_consumer import StreamConsumer
from vyomcloudbridge.services.vyom_listener import VyomListener
from vyomcloudbridge.utils.install_specs import InstallSpecs
from typing import Dict, Type


AVAILABLE_SERVICES: Dict[str, Type] = {
    "queueworker": QueueWorker,
    "dirwatcher": DirWatcher,
    "streamconsumer": StreamConsumer,
    "missionstats": MissionStats,
    "machinestats": MachineStats,
    "vyomlistener": VyomListener,
}

install_specs = InstallSpecs()
if install_specs.is_full_install:
    from vyomcloudbridge.services.mavproxy_hq import MavproxyHq
    from vyomcloudbridge.services.ros_publisher import RosPublisher
    from vyomcloudbridge.services.robot_stats import RobotStat

    AVAILABLE_SERVICES["mavproxyhq"] = MavproxyHq
    AVAILABLE_SERVICES["rospublisher"] = RosPublisher
    AVAILABLE_SERVICES["robotstat"] = RobotStat
