import unittest.mock
from unittest import TestCase
from unittest.mock import Mock, patch, call

from mock import GPIO
from mock.ibs import IBS
from src.cleaning_robot import CleaningRobot


class TestCleaningRobot(TestCase):

    def test_initialize_robot(self):
        #Arrange
        r = CleaningRobot()
        #Act
        r.initialize_robot()
        #assert
        self.assertEqual("0,0,N", r.robot_status())

    @patch.object(IBS, "get_charge_left")
    @patch.object(GPIO, "output")
    def test_manage_clean_system_when_charge_less_than_10_percent(self, mock_ibs: Mock, mock_output: Mock):
        mock_ibs.return_value = 9
        r = CleaningRobot()
        r.initialize_robot()
        r.manage_cleaning_system()
        mock_output.assert_has_calls([
            unittest.mock.call(12, True),
            unittest.mock.call(13, False)
        ])
        self.assertEqual(r.recharge_led_on, True)
        self.assertEqual(r.cleaning_system_on, False)



