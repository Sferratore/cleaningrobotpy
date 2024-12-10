
import time

DEPLOYMENT = False  # This variable is to understand whether you are deploying on the actual hardware

try:
    import RPi.GPIO as GPIO
    import board
    import IBS
    DEPLOYMENT = True
except:
    import mock.GPIO as GPIO
    import mock.board as board
    import mock.ibs as IBS


class CleaningRobot:

    LED_GARBAGE_BAG = 6
    LED_SOAP_CONTAINER = 7
    LED_WATER_CONTAINER = 8
    GARBAGE_BAG_PIN = 9
    SOAP_CONTAINER_PIN = 10
    WATER_CONTAINER_PIN = 11
    RECHARGE_LED_PIN = 12
    CLEANING_SYSTEM_PIN = 13
    INFRARED_PIN = 15


    # Wheel motor pins
    PWMA = 16
    AIN2 = 18
    AIN1 = 22

    # Rotation motor pins
    BIN1 = 29
    BIN2 = 31
    PWMB = 32
    STBY = 33

    N = 'N'
    S = 'S'
    E = 'E'
    W = 'W'

    LEFT = 'l'
    RIGHT = 'r'
    FORWARD = 'f'

    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.INFRARED_PIN, GPIO.IN)
        GPIO.setup(self.RECHARGE_LED_PIN, GPIO.OUT)
        GPIO.setup(self.CLEANING_SYSTEM_PIN, GPIO.OUT)

        GPIO.setup(self.PWMA, GPIO.OUT)
        GPIO.setup(self.AIN2, GPIO.OUT)
        GPIO.setup(self.AIN1, GPIO.OUT)
        GPIO.setup(self.PWMB, GPIO.OUT)
        GPIO.setup(self.BIN2, GPIO.OUT)
        GPIO.setup(self.BIN1, GPIO.OUT)
        GPIO.setup(self.STBY, GPIO.OUT)

        ic2 = board.I2C()
        self.ibs = IBS.IBS(ic2)

        self.pos_x = None
        self.pos_y = None
        self.heading = None

        self.recharge_led_on = False
        self.cleaning_system_on = False

        self.garbage_bag_led_on = False
        self.garbage_bag_resource_available = False

        self.soap_container_led_on = False
        self.soap_container_resource_available = False

        self.water_container_led_on = False
        self.water_container_resource_available = False

    def initialize_robot(self) -> None:
        self.pos_x = 0
        self.pos_y = 0
        self.heading = self.N

    def robot_status(self) -> str:
        return f"{self.pos_x},{self.pos_y},{self.heading}"

    def execute_command(self, command: str) -> str:
        self.manage_cleaning_system()
        if (not self.cleaning_system_on and self.recharge_led_on):
            return f"!({self.pos_x},{self.pos_y},{self.heading})"
        if command == self.FORWARD:
            if self.obstacle_found():
                if self.heading == self.E:
                    return f"({self.pos_x},{self.pos_y},{self.heading})({self.pos_x+1},{self.pos_y})"
                elif self.heading == self.W:
                    return f"({self.pos_x},{self.pos_y},{self.heading})({self.pos_x-1},{self.pos_y})"
                elif self.heading == self.N:
                    return f"({self.pos_x},{self.pos_y},{self.heading})({self.pos_x},{self.pos_y+1})"
                elif self.heading == self.S:
                    return f"({self.pos_x},{self.pos_y},{self.heading})({self.pos_x},{self.pos_y-1})"
            else:
                self.activate_wheel_motor()
                if self.heading == self.E:
                    self.pos_x += 1;
                elif self.heading == self.W:
                    self.pos_x += -1
                elif self.heading == self.N:
                    self.pos_y += 1
                elif self.heading == self.S:
                    self.pos_y += -1
                else:
                    raise CleaningRobotError("Heading is not a correct value.")
        elif command == self.LEFT:
            self.activate_rotation_motor(self.LEFT)
            self.heading = self.W if self.heading == self.N else self.N
        elif command == self.RIGHT:
            self.activate_rotation_motor(self.RIGHT)
            self.heading = self.E if self.heading == self.N else self.N
        else:
            raise CleaningRobotError("Invalid command")
        return self.robot_status()

    def obstacle_found(self) -> bool:
        return GPIO.input(self.INFRARED_PIN)

    def manage_cleaning_system(self) -> None:
        charge_left = self.ibs.get_charge_left()
        if charge_left < 10:
            GPIO.output(self.RECHARGE_LED_PIN, True)
            GPIO.output(self.CLEANING_SYSTEM_PIN, False)
            self.recharge_led_on = True
            self.cleaning_system_on = False
        else:
            GPIO.output(self.RECHARGE_LED_PIN, False)
            GPIO.output(self.CLEANING_SYSTEM_PIN, True)
            self.recharge_led_on = False
            self.cleaning_system_on = True

    def activate_wheel_motor(self) -> None:
        """
        Let the robot move forward by activating its wheel motor
        """
        # Drive the motor clockwise
        GPIO.output(self.AIN1, GPIO.HIGH)
        GPIO.output(self.AIN2, GPIO.LOW)
        # Set the motor speed
        GPIO.output(self.PWMA, GPIO.HIGH)
        # Disable STBY
        GPIO.output(self.STBY, GPIO.HIGH)

        if DEPLOYMENT: # Sleep only if you are deploying on the actual hardware
            time.sleep(1) # Wait for the motor to actually move

        # Stop the motor
        GPIO.output(self.AIN1, GPIO.LOW)
        GPIO.output(self.AIN2, GPIO.LOW)
        GPIO.output(self.PWMA, GPIO.LOW)
        GPIO.output(self.STBY, GPIO.LOW)

    def activate_rotation_motor(self, direction) -> None:
        """
        Let the robot rotate towards a given direction
        :param direction: "l" to turn left, "r" to turn right
        """
        if direction == self.LEFT:
            GPIO.output(self.BIN1, GPIO.HIGH)
            GPIO.output(self.BIN2, GPIO.LOW)
        elif direction == self.RIGHT:
            GPIO.output(self.BIN1, GPIO.LOW)
            GPIO.output(self.BIN2, GPIO.HIGH)

        GPIO.output(self.PWMB, GPIO.HIGH)
        GPIO.output(self.STBY, GPIO.HIGH)

        if DEPLOYMENT:  # Sleep only if you are deploying on the actual hardware
            time.sleep(1)  # Wait for the motor to actually move

        # Stop the motor
        GPIO.output(self.BIN1, GPIO.LOW)
        GPIO.output(self.BIN2, GPIO.LOW)
        GPIO.output(self.PWMB, GPIO.LOW)
        GPIO.output(self.STBY, GPIO.LOW)

    def check_garbage_bag(self) -> bool:
        self.garbage_bag_resource_available = GPIO.input(self.GARBAGE_BAG_PIN)
        if not self.garbage_bag_resource_available:
            GPIO.output(self.LED_GARBAGE_BAG, True)
            self.garbage_bag_led_on = True
        else:
            GPIO.output(self.LED_GARBAGE_BAG, False)
            self.garbage_bag_led_on = False
        return self.garbage_bag_resource_available

    def check_soap_container(self) -> bool:
        self.soap_container_resource_available = GPIO.input(self.SOAP_CONTAINER_PIN)
        if not self.soap_container_resource_available:
            GPIO.output(self.LED_SOAP_CONTAINER, True)
            self.soap_container_led_on = True
        else:
            GPIO.output(self.LED_SOAP_CONTAINER, False)
            self.soap_container_led_on = False
        return self.soap_container_resource_available

    def check_water_container(self) -> bool:
        pass


class CleaningRobotError(Exception):
    pass

