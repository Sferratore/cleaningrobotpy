import unittest.mock
from platform import system
from unittest import TestCase
from unittest.mock import Mock, patch, call, MagicMock

from mock import GPIO
from mock.ibs import IBS
from src.cleaning_robot import CleaningRobot, CleaningRobotError


class TestCleaningRobot(TestCase):

    def test_initialize_robot(self):
        #Arrange
        r = CleaningRobot()
        #Act
        r.initialize_robot()
        #assert
        self.assertEqual("0,0,N", r.robot_status())


    @patch.object(GPIO, "output")
    @patch.object(IBS, "get_charge_left")
    def test_manage_clean_system_when_charge_less_than_10_percent(self, mock_ibs: Mock, mock_output: Mock):
        mock_ibs.side_effect = [9]  # Per qualche motivo mi veniva restituito un oggetto MagicMock con return_value. Ho quindi usato side_effect
        r = CleaningRobot()
        r.initialize_robot()
        r.manage_cleaning_system()
        mock_output.assert_has_calls([
            unittest.mock.call(12, True),
            unittest.mock.call(13, False)
        ])
        self.assertEqual(r.recharge_led_on, True)
        self.assertEqual(r.cleaning_system_on, False)

    @patch.object(GPIO, "output")
    @patch.object(IBS, "get_charge_left")
    def test_manage_clean_system_when_charge_less_than_10_percent(self, mock_ibs: Mock, mock_output: Mock):
        mock_ibs.side_effect = [11]  # Per qualche motivo mi veniva restituito un oggetto MagicMock con return_value. Ho quindi usato side_effect
        r = CleaningRobot()
        r.initialize_robot()
        r.manage_cleaning_system()
        mock_output.assert_has_calls([
            unittest.mock.call(12, False),
            unittest.mock.call(13, True)
        ])
        self.assertEqual(r.recharge_led_on, False)
        self.assertEqual(r.cleaning_system_on, True)

    @patch.object(CleaningRobot, "check_cleaning_resources")
    @patch.object(IBS, "get_charge_left")
    @patch.object(CleaningRobot, "activate_wheel_motor")
    def test_execute_command_move_forward(self, mock_wheel: Mock, mock_ibs: Mock, mock_ccr: Mock):
        mock_ibs.side_effect = [100]
        mock_ccr.return_value = True
        r = CleaningRobot()
        r.initialize_robot()
        result = r.execute_command("f")
        mock_wheel.assert_called()
        mock_ccr.assert_called()
        self.assertEqual(result, "0,1,N")

    @patch.object(CleaningRobot, "check_cleaning_resources")
    @patch.object(IBS, "get_charge_left")
    @patch.object(CleaningRobot, "activate_rotation_motor")
    def test_execute_command_move_right(self, mock_rotation: Mock, mock_ibs: Mock, mock_ccr: Mock):
        mock_ibs.side_effect = [100]
        mock_ccr.return_value = True
        r = CleaningRobot()
        r.initialize_robot()
        result =r.execute_command("r")
        mock_rotation.assert_called_once_with("r")
        mock_ccr.assert_called()
        self.assertEqual(result, "0,0,E")

    @patch.object(CleaningRobot, "check_cleaning_resources")
    @patch.object(IBS, "get_charge_left")
    @patch.object(CleaningRobot, "activate_rotation_motor")
    def test_execute_command_move_left(self, mock_rotation: Mock, mock_ibs: Mock, mock_ccr: Mock):
        mock_ibs.side_effect = [100]
        mock_ccr.return_value = True
        r = CleaningRobot()
        r.initialize_robot()
        result = r.execute_command("l")
        mock_rotation.assert_called_once_with("l")
        mock_ccr.assert_called()
        self.assertEqual(result, "0,0,W")

    @patch.object(CleaningRobot, "check_cleaning_resources")
    @patch.object(IBS, "get_charge_left")
    @patch.object(CleaningRobot, "activate_wheel_motor")
    @patch.object(CleaningRobot, "activate_rotation_motor")
    def test_execute_command_move_more_than_once(self, mock_rotation: Mock, mock_wheel: Mock, mock_ibs: Mock, mock_ccr: Mock):
        mock_ibs.side_effect = [100, 99, 99]
        mock_ccr.side_effect = [True, True, True]
        r = CleaningRobot()
        r.initialize_robot()
        r.execute_command("f")
        r.execute_command("r")
        result = r.execute_command("f")
        mock_rotation.assert_called_once_with("r")
        mock_wheel.assert_has_calls([
            unittest.mock.call(),
            unittest.mock.call()
        ])
        mock_ccr.assert_called()
        self.assertEqual(result, "1,1,E")

    @patch.object(CleaningRobot, "check_cleaning_resources")
    @patch.object(IBS, "get_charge_left")
    def test_execute_command_wrong_command(self, mock_ibs: Mock, mock_ccr: Mock):
        mock_ibs.side_effect = [100]
        mock_ccr.return_value = True
        r = CleaningRobot()
        r.initialize_robot()
        mock_ccr.assert_called()
        self.assertRaises(CleaningRobotError, r.execute_command, "a")

    @patch.object(CleaningRobot, "check_cleaning_resources")
    def test_execute_command_when_cleaning_resources_not_ok(self, mock_ccr: Mock):
        mock_ccr.return_value = False
        r = CleaningRobot()
        r.initialize_robot()
        result = r.execute_command("f")
        mock_ccr.assert_called()
        self.assertEqual(result, "0,0,N")

    @patch.object(GPIO, "input")
    def test_obstacle_found(self, mock_input: Mock):
        mock_input.side_effect = [True, False]
        r = CleaningRobot()
        r.initialize_robot()
        result = r.obstacle_found()
        result2 = r.obstacle_found()
        mock_input.assert_has_calls([
            unittest.mock.call(15),
            unittest.mock.call(15)
        ])
        self.assertTrue(result)
        self.assertFalse(result2)

    @patch.object(IBS, "get_charge_left")
    @patch.object(CleaningRobot, "obstacle_found")
    def test_obstacle_detecting_in_execute_command(self, mock_obstacle: Mock, mock_ibs: Mock):
        mock_ibs.side_effect = [100]
        mock_obstacle.side_effect = [True]
        r = CleaningRobot()
        r.initialize_robot()
        result = r.execute_command("f")
        mock_obstacle.assert_called()
        self.assertEqual(result, "(0,0,N)(0,1)")

    @patch.object(IBS, "get_charge_left")
    def test_execute_command_when_battery_is_under_10(self, mock_ibs: Mock):
        mock_ibs.side_effect = [9]
        r = CleaningRobot()
        r.manage_cleaning_system = MagicMock(wraps=r.manage_cleaning_system) #  I substituted the original method with the MagicMock version that still has the original code inside thanks to the wrap, so that I can mock without having problems in the usage. If you use @patch.object on this, it breaks!!
        r.initialize_robot()
        result = r.execute_command("f")
        r.manage_cleaning_system.assert_called() # Checking that method has been called :)
        self.assertEqual(result, "!(0,0,N)")

    @patch.object(GPIO, "output")
    @patch.object(GPIO, "input")
    def test_check_garbage_bag_when_not_full(self, mock_garbage_pin: Mock, mock_garbage_led: Mock):
        mock_garbage_pin.return_value = True
        r = CleaningRobot()
        r.check_garbage_bag()
        mock_garbage_pin.assert_called_once_with(9)
        mock_garbage_led.assert_called_once_with(6, False)
        self.assertTrue(r.garbage_bag_resource_available)
        self.assertFalse(r.garbage_bag_led_on)

    @patch.object(GPIO, "output")
    @patch.object(GPIO, "input")
    def test_check_garbage_bag_when_full(self, mock_garbage_pin: Mock, mock_garbage_led: Mock):
        mock_garbage_pin.return_value = False
        r = CleaningRobot()
        r.check_garbage_bag()
        mock_garbage_pin.assert_called_once_with(9)
        mock_garbage_led.assert_called_once_with(6, True)
        self.assertFalse(r.garbage_bag_resource_available)
        self.assertTrue(r.garbage_bag_led_on)

    @patch.object(GPIO, "output")
    @patch.object(GPIO, "input")
    def test_check_soap_container_when_not_empty(self, mock_soap_pin: Mock, mock_soap_led: Mock):
        mock_soap_pin.return_value = True
        r = CleaningRobot()
        r.check_soap_container()
        mock_soap_pin.assert_called_once_with(10)
        mock_soap_led.assert_called_once_with(7, False)
        self.assertTrue(r.soap_container_resource_available)
        self.assertFalse(r.soap_container_led_on)

    @patch.object(GPIO, "output")
    @patch.object(GPIO, "input")
    def test_check_soap_container_when_empty(self, mock_soap_pin: Mock, mock_soap_led: Mock):
        mock_soap_pin.return_value = False
        r = CleaningRobot()
        r.check_soap_container()
        mock_soap_pin.assert_called_once_with(10)
        mock_soap_led.assert_called_once_with(7, True)
        self.assertFalse(r.soap_container_resource_available)
        self.assertTrue(r.soap_container_led_on)

    @patch.object(GPIO, "output")
    @patch.object(GPIO, "input")
    def test_check_water_container_when_not_empty(self, mock_water_pin: Mock, mock_water_led: Mock):
        mock_water_pin.return_value = True
        r = CleaningRobot()
        r.check_water_container()
        mock_water_pin.assert_called_once_with(11)
        mock_water_led.assert_called_once_with(8, False)
        self.assertTrue(r.water_container_resource_available)
        self.assertFalse(r.water_container_led_on)

    @patch.object(GPIO, "output")
    @patch.object(GPIO, "input")
    def test_check_water_container_when_empty(self, mock_water_pin: Mock, mock_water_led: Mock):
        mock_water_pin.return_value = False
        r = CleaningRobot()
        r.check_water_container()
        mock_water_pin.assert_called_once_with(11)
        mock_water_led.assert_called_once_with(8, True)
        self.assertFalse(r.water_container_resource_available)
        self.assertTrue(r.water_container_led_on)

    @patch.object(CleaningRobot, "check_water_container")
    @patch.object(CleaningRobot, "check_soap_container")
    @patch.object(CleaningRobot, "check_garbage_bag")
    def test_check_cleaning_resources_when_ok(self, mock_garbage: Mock, mock_soap: Mock, mock_water: Mock):
        mock_garbage.return_value = True
        mock_soap.return_value = True
        mock_water.return_value = True
        r = CleaningRobot()
        result = r.check_cleaning_resources()
        mock_garbage.assert_called()
        mock_soap.assert_called()
        mock_water.assert_called()
        self.assertTrue(result)

    @patch.object(CleaningRobot, "check_water_container")
    @patch.object(CleaningRobot, "check_soap_container")
    @patch.object(CleaningRobot, "check_garbage_bag")
    def test_check_cleaning_resources_when_not_ok(self, mock_garbage: Mock, mock_soap: Mock, mock_water: Mock):
        mock_garbage.return_value = True
        mock_soap.return_value = False
        mock_water.return_value = True
        r = CleaningRobot()
        result = r.check_cleaning_resources()
        mock_garbage.assert_called()
        mock_soap.assert_called()
        mock_water.assert_called()
        self.assertFalse(result)

    @patch.object(CleaningRobot, "check_cleaning_resources")
    def test_check_cleaning_resources_in_initialize_robot(self, mock_ccr: Mock):
        mock_ccr.return_value = True
        r = CleaningRobot()
        r.initialize_robot()
        mock_ccr.assert_called()

