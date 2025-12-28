# Standard library imports
import random
import string
import time
import uuid
import threading

# Third-party imports
from pymavlink import mavutil
import importlib
import sys
import json
from rosidl_runtime_py.convert import message_to_ordereddict
from std_msgs.msg import String

# Local application imports
from vyomcloudbridge.constants.constants import DUMMY_DATA_DT_SRC
from vyomcloudbridge.utils.abc_sender import AbcSender
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.shared_memory import SharedMemoryUtil

import os


class MavSender(AbcSender):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MavSender, cls).__new__(cls)
                    print("MavSender singleton initialized")
        print("MavSender client service started")
        return cls._instance

    def __init__(self, log_level=None):
        try:
            if getattr(self, "_initialized", False):
                return
            self._initialized = True

            super().__init__(log_level=log_level)
            self.log_level = log_level
            self.logger.info("MavSender initializing...")

            # compulsory
            self.channel = "mavlink"
            self.combine_by_target_id = True

            # machine configs
            self.machine_config = Configs.get_machine_config()
            self.machine_id = self.machine_config.get("machine_id", "-") or "-"

            # class specific
            self.mission_id = 0
            self.user_id = 1
            self.mission_status = 2
            self.chunk_retry_count = 3
            self.chunk_retry_timeout = 5
            self.chunk_result_recheck_delay = 0.1
            self.udp_connection_timeout = 5
            self.udp_heartbeat_timeout = 5

            self.received_ack_messages = {}
            # self.listener.start() # AMAR

            print(os.path.dirname(mavutil.__file__))

            # MAVLink connection setup
            self.master = mavutil.mavlink_connection(
                # vyom_settings.MAVLINK_COMMANDER_IP,
                "udp:127.0.0.1:14556",
                source_system=156,
                source_component=191,
                dialect="ardupilotmega",
            )
            self.master.wait_heartbeat(timeout=self.udp_heartbeat_timeout)

            self.logger.info("Heart beat received. MavSender initialized successfully!")

        except Exception as e:
            self.logger.error(f"Error init MavSender: {str(e)}")
            raise

    def get_ack_data_received(self, msgid, chunk_index):  # AMAR
        """
        Get shared acknowledgment data from shared memory
        """
        shared_mem = SharedMemoryUtil(log_level=self.log_level)
        shared_mem.cleanup_old_shared_memory()
        data = shared_mem.get_data(f"mavlink_ack_data-{msgid}-{chunk_index}")

        return data is not None

    def serialise_msg(self, message):
        # If it's a string or dict, treat accordingly
        if isinstance(message, str):
            return json.dumps(dict(typ="string", msg=message))

        elif isinstance(message, dict):
            return json.dumps(dict(typ="dict", msg=message))

        else:
            msg_type = type(message).__name__
            msg_to_sent = message_to_ordereddict(message)
            return json.dumps(dict(typ=msg_type, msg=msg_to_sent))

    def send_ros_message(self, ros_message, msg_type):
        # function to get current mission status
        # TODO : create a function either to listen to the mission msgs or get from parameters

        cloud_mav_pub = self.create_publisher(msg_type, "cloud_mav_msg", 10)

        cloud_mav_pub.publish(ros_message)
        self.logger().info(f"Publishing: {ros_message}")

    def send_one_chunk(self, chunk_count, chunk, chunk_index, msgid):
        self.logger.debug(
            f"send_one_chunk called with -> chunk_count: {chunk_count}, chunk_index: {chunk_index}, "
            f"msgid: {msgid}, chunk: {chunk}"
        )

        try:
            timestamp = int(time.time())
            self.master.mav.vyom_message_send(
                0,  # target_system
                0,  # target_component
                msgid.encode("utf-8"),  # 6-byte message_id
                chunk,  # The 233-byte msg_text
                chunk_count,  # Total number of chunks
                chunk_index,  # Current chunk index
                timestamp,  # Unix timestamp
            )
            self.logger.debug(
                f"Sent chunk {chunk_index+1}/{chunk_count} for msgid: {msgid}"
            )
        except Exception as e:
            self.logger.warning(
                f"Failed to send chunk {chunk_index+1}/{chunk_count} for msgid: {msgid}. Error: {e}"
            )
            importlib.reload(mavutil)

        # sleep for a short time to allow the listener to process the message and sent msgs properly
        # NOTE : 0.1 was oberved to be a good value. 0.01 was not enough
        # time.sleep(0.1)

    def get_missing_chunk_indexes(self, msg_id, chunk_count):  # AMAR

        missing = []

        for chunk_index in range(chunk_count):
            ack_data = self.get_ack_data_received(msg_id, chunk_index)
            if not ack_data:
                missing.append(chunk_index)

        return missing

    def send_all_chunks_with_retries(self, chunk_count, chunks, current_msgid):

        max_resends = 10
        missing_chunks = list(range(chunk_count))

        for attempt in range(1, max_resends + 1):

            for chunk_index in missing_chunks:
                try:
                    self.send_one_chunk(
                        chunk_count, chunks[chunk_index], chunk_index, current_msgid
                    )
                except Exception as e:
                    self.logger.error(
                        f"Failed to send chunk {chunk_index+1}/{chunk_count} for msgid: {current_msgid}. Error: {e}"
                    )
            time.sleep(0.2)
            self.logger.debug(
                f"Sending message, attempt: {attempt} for missing {len(missing_chunks)} acks, msgid= {current_msgid}"
            )

            # refreshing missing chunk indexes after sending chunks
            missing_chunks = self.get_missing_chunk_indexes(current_msgid, chunk_count)

            if not missing_chunks:
                self.logger.debug("All chunks acknowledged.")
                break

        # TODO popping later
        # self.listener.ack_data_received.pop(current_msgid, None) # AMAR
        # shared_mem = SharedMemoryUtil(log_level=self.log_level)
        # ack_data = shared_mem.get_data(f"mavlink_ack_data-{current_msgid}-{chunk_index}")

        # if "mavlink_ack_data" in ack_data and current_msgid in ack_data.get(
        #     "mavlink_ack_data", {}
        # ):
        #     ack_data["mavlink_ack_data"].pop(current_msgid, None)
        #     shared_mem.set_data(ack_data)

        if missing_chunks:
            self.logger.warning(f"Still missing ACKs after retries: {missing_chunks}")
            return False
        return True

    def create_chunks(self, message):
        max_chunk_size = 233
        chunks = [
            message[i : i + max_chunk_size]
            for i in range(0, len(message), max_chunk_size)
        ]
        total_chunks = len(chunks)

        return chunks, total_chunks

    def msgid_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return "".join(random.choice(chars) for _ in range(size))

    def send_mav_message(self, message, destination_id):
        chunks, chunk_count = self.create_chunks(message)

        # temporarily using time
        current_msgid = self.msgid_generator()

        self.logger.debug(f"Sending message to GCS... {message}...")
        
        return self.send_all_chunks_with_retries(chunk_count, chunks, current_msgid)

    def send_message(
        self,
        message,
        message_type,
        data_source,
        target_des_id,
        destination_id,
        source_id,
        topic,
    ):
        """
        Send message to one target using the appropriate communication channel.

        Args:
            destinations (str): Destination group (e.g. 's3', 'gcs_mqtt').
            message (ROS 2 message): ROS msg for now ( will add files later)
            message_type (str): Type of message ("ros", "json", "string").
        """
        # Case 1 - Internal ROS 2 message
        # self.send_ros_message(message, message_type)

        # Get the first target (device_id, channel)
        # target = self.extract_destination_id(destinations)

        # if not target:
        #     return

        # device_id, channel = target

        try:
            result = self.send_mav_message(message, destination_id)
            if result:
                self.logger.info(
                    f"Message successfully sent to target_des_id-{target_des_id}, having topic-{topic}"
                )
            else:
                self.logger.error(
                    f"Failed to send message to target_des_id-{target_des_id}, having topic-{topic}"
                )

            return result
        except Exception as e:
            self.logger.error(
                f"sending message {topic} to {target_des_id} failed: {str(e)}"
            )
            return False

        # elif channel == "mavlink":
        #     self.send_mav_message(message, device_id)

        # else:
        #     self.logger().warn(
        #         f"Unknown channel '{channel}' for device '{device_id}'"
        #     )

    def cleanup(self):
        # TODO: Implement connection cleanup: To check if this works
        try:
            if self.master:
                self.master.close()
                self.logger.info("MAVLink connection closed successfully.")
        except Exception as e:
            self.logger.error(f"Error closing MAVLink connection: {str(e)}")

        # self.listener.stop() # AMAR

    def is_healthy(self):
        # TODO Implement if connection is working
        # return true
        # else false
        pass


def main():
    sender = MavSender()

    # NOTE: Types of msgs sent are string, dict and ros msg

    # Example message
    test_message = String()
    # test_message.data = "Test Message for communication"
    # test_message.data = "Kinematics and dynamics: kinematics and dynamics are two fundamental aspects that deal with the motion and behavior of robotic systems. Kinematics is the study of the motion of objects without considering the forces that cause the motion, focusing on describing the position, velocity, and acceleration of robotic systems without regard to the forces and torques that produce those motions. To completely define the pose of a robot we need to know the position and orientation of each link coordinate frame with respect to the base frame or a world coordinate system. Computing kinematics can be declined in two different sub problems in case of a robot manipulator: finding the pose of the end effector (hand) given the joint variables values of the robot, and this goes by the name Forward Kinematics; or, with increased complexity, to calculate the joint variables values of the robot given the pose of the end effector, namely computing its Inverse Kinematics. Dynamics, on the other hand, is concerned with the forces and torques that cause motion in robotic systems. It involves the study of how forces and torques affect the motion of robots, including their accelerations and resulting velocities."

    # test_message.data= "Humanoid robots are robots that look like or mimic human behavior. These robots usually perform human-like activities (like running, jumping and carrying objects), and are sometimes designed to look like us, even having human faces and expressions. Two of the most prominent examples of humanoid robots are Hanson Robotics’ Sophia and Boston Dynamics’ Atlas. Cobots, or collaborative robots, are robots designed to work alongside humans. These robots prioritize safety by using sensors to remain aware of their surroundings, executing slow movements and ceasing actions when their movements are obstructed. Cobots typically perform simple tasks, freeing up humans to address more complex work. Industrial robots automate processes in manufacturing environments like factories and warehouses. Possessing at least one robotic arm, these robots are made to handle heavy objects while moving with speed and precision. As a result, industrial robots often work in assembly lines to boost productivity. Medical robots assist healthcare professionals in various scenarios and support the physical and mental health of humans. These robots rely on AI and sensors to navigate healthcare facilities, interact with humans and execute precise movements. Some medical robots can even converse with humans, encouraging people’s social and emotional growth. Agricultural robots handle repetitive and labor-intensive tasks, allowing farmers to use their time and energy more efficiently. These robots also operate in greenhouses, where they monitor crops and help with harvests. Agricultural robots come in many forms, ranging from autonomous tractors to drones that collect data for farmers to analyze. Microrobotics is the study and development of robots on a miniature scale. Often no bigger than a millimeter, microrobots can vary in size, depending on the situation. Biotech researchers typically use microrobotics to monitor and treat diseases, with the goal of improving diagnostic tools and creating more targeted solutions. Augmenting robots, also known as VR robots, either enhance current human capabilities or replace the capabilities a human may have lost. The field of robotics for human augmentation is a field where science fiction could become reality very soon, with bots that have the ability to redefine the definition of humanity by making humans faster and stronger. Some examples of current augmenting robots are robotic prosthetic limbs or exoskeletons used to lift hefty weights. Software bots, or simply ‘bots,’ are computer programs which carry out tasks autonomously. They are not technically considered robots. One common use case of software robots is a chatbot, which is a computer program that simulates conversation both online and over the phone and is often used in customer service scenarios. Chatbots can either be simple services that answer questions with an automated response or more complex digital assistants that learn from user information."

    test_message.data = (
        5
        * "Like any eir plusses and negatives. Here’s a breakdown of the good and bad about robots and the future of robotics. Advantages: They work in hazardous environments: Why risk human lives when you can send a robot in to do the job? Consider how preferable it is to have a robot fighting a fire or working on a nuclear reactor core. They’re cost-effective: Robots don’t take sick days or coffee breaks, nor need perks like life insurance, paid time off, or healthcare offerings like dental and vision. They increase productivity: Robots are wired to perform repetitive tasks ad infinitum; the human brain is not. Industries use robots to accomplish the tedious, redundant work, freeing employees to tackle more challenging tasks and even learn new skills. They offer better quality assurance: Vigilance decrement is a lapse in concentration that hits workers who repeatedly perform the same functions. As the human’s concentration level drops, the likelihood of errors, poor results, or even accidents increases. Robots perform repetitive tasks flawlessly without having their performance slip due to boredom. Disadvantages: They incur deep startup costs: Robot implementation is an investment risk, and it costs a lot. Although most manufacturers eventually see a recoup of their investment over the long run, it's expensive in the short term. However, this is a common obstacle in new technological implementation, like setting up a wireless network or performing cloud migration. They might take away jobs: Yes, some people have been replaced by robots in certain situations, like assembly lines, for instance. Whenever the business sector incorporates game-changing technology, some jobs become casualties. However, this disadvantage might be overstated because robot implementation typically creates a greater demand for people to support the technology, which brings up the final disadvantage. They require companies to hire skilled support staff: This drawback is good news for potential employees, but bad news for thrifty-minded companies. Robots require programmers, operators, and repair personnel. While job seekers may rejoice, the prospect of having to recruit professionals (and pay professional-level salaries!) may serve as an impediment to implementing robots. The Future of Robotics: What’s the Use of AI in Robotics? Artificial Intelligence (AI) increases human-robot interaction, collaboration opportunities, and quality. The industrial sector already has co-bots, which are robots that work alongside humans to perform testing and assembly. Advances in AI help robots mimic human behavior more closely, which is why they were created in the first place. Robots that act and think more like people can integrate better into the workforce and bring a level of efficiency unmatched by human employees. Robot designers use Artificial Intelligence to give their Humanoid robots are robots that look like or mimic human behavior. These robots usually perform human-like activities (like running, jumping and carrying objects), and are sometimes designed to look like us, even having human faces and expressions. Two of the most prominent examples of humanoid robots are Hanson Robotics’ Sophia and Boston Dynamics’ Atlas. Cobots, or collaborative robots, are robots designed to work alongside humans. These robots prioritize safety by using sensors to remain aware of their surroundings, executing slow movements and ceasing actions when their movements are obstructed. Cobots typically perform simple tasks, freeing up humans to address more complex work. Industrial robots automate processes in manufacturing environments like factories and warehouses. Possessing at least one robotic arm, these robots are made to handle heavy objects while moving with speed and precision. As a result, industrial robots often work in assembly lines to boost productivity. Medical robots assist healthcare professionals in various scenarios and support the physical and mental health of humans. These robots rely on AI and sensors to navigate healthcare facilities, interact with humans and execute precise movements. Some medical robots can even converse with humans, encouraging people’s social and emotional growth. Agricultural robots handle repetitive and labor-intensive tasks, allowing farmers to use their time and energy more efficiently. These robots also operate in greenhouses, where they monitor crops and help with harvests. Agricultural robots come in many forms, ranging from autonomous tractors to drones that collect data for farmers to analyze. Microrobotics is the study and development of robots on a miniature scale. Often no bigger than a millimeter, microrobots can vary in size, depending on the situation. Biotech researchers typically use microrobotics to monitor and treat diseases, with the goal of improving diagnostic tools and creating more targeted solutions. Augmenting robots, also known as VR robots, either enhance current human capabilities or replace the capabilities a human may have lost. The field of robotics for human augmentation is a field where science fiction could become reality very soon, with bots that have the ability to redefine the definition of humanity by making humans faster and stronger. Some examples of current augmenting robots are robotic prosthetic limbs or exoskeletons used to lift hefty weights. Software bots, or simply ‘bots,’ are computer programs which carry out tasks autonomously. They are not technically considered robots. One common use case of software robots is a chatbot, which is a computer program that simulates conversation both online and over the phone and is often used in customer service scenarios. Chatbots can either be simple services that answer questions with an automated response or more complex digital assistants that learn from  creations enhanced capabilities like: Computer Vision: Robots can identify and recognize objects they meet, discern details, and learn how to navigate or avoid specific items. Manipulation: AI helps robots gain the fine motor skills needed to grasp objects without destroying the item. Motion Control and Navigation: Robots no longer need humans to guide them along paths and process flows. AI enables robots to analyze their environment and self-navigate. This capability even applies to the virtual world of software. AI helps robot software processes avoid flow bottlenecks or process exceptions. Natural Language Processing (NLP) and Real-World Perception: Artificial Intelligence and Machine Learning (ML) help robots better understand their surroundings, recognize and identify patterns, and comprehend data. These improvements increase the robot’s autonomy and decrease reliance on human agents. A Word About Robot Software: Software robots are computer programs that perform tasks without human intervention, such as web crawlers or chatbots. These robots are entirely virtual and not considered actual robots since they have no physical characteristics. This technology shouldn't be confused with robotic software loaded into a robot and determines its programming. However, it's normal to experience overlap between the two entities since, in both cases, the software is helping the entity (robot or computer program) perform its functions independent of human interaction. The Future of Robotics and Robots: Thanks to improved sensor technology and more remarkable advances in Machine Learning and Artificial Intelligence, robots will keep moving from mere rote machines to collaborators with cognitive functions. These advances, and other associated fields, are enjoying an upwards trajectory, and robotics will significantly benefit from these strides. We can expect to see more significant numbers of increasingly sophisticated robots incorporated into more areas of life, working with humans. Contrary to dystopian-minded prophets of doom, these improved robots will not replace workers. Industries rise and fall, and some become obsolete in the face of new technologies, bringing new opportunities for employment and education. That’s the case with robots. Perhaps there will be fewer human workers welding automobile frames, but there will be a greater need for skilled technicians to program, maintain, and repair the machines. In many cases, this means that employees could receive valuable in-house training and upskilling, giving them a set of skills that could apply to robot programming and maintenance and other fields and industries. The Future of Robotics: How Robots Will Change the World: Robots will increase economic growth and productivity and create new career opportunities for many people worldwide. However, there are still warnings out there about massive job losses, forecasting losses of 20 million manufacturing jobs by 2030, or how 30% of all jobs could be automated by 2030. But thanks to the consistent levels of precision that robots offer, we can look forward to robots handling more of the burdensome, redundant manual labor tasks, making transportation work more efficiently, improving healthcare, and freeing people to improve themselves. But, of course, time will tell how this all works out. Choose the Right Program: Supercharge your career in AI and ML with Simplilearn's comprehensive courses. Gain the skills and knowledge to transform industries and unleash your true potential. Enroll now."
    )
    print(f"Length of msg sent: {len(test_message.data)}")
    destination_id = "MSG001"

    # Send via MAVLink/GCS
    print(
        sender.send_message(
            data_source=DUMMY_DATA_DT_SRC,  # Replace with actual value
            target_des_id="target_device_id",  # Replace with actual target ID
            destination_id=destination_id,
            source_id=1,
            message=test_message,
            message_type="gcs_mav",
            topic="example_topic",
        )
    )

    sender.cleanup()


if __name__ == "__main__":
    main()
