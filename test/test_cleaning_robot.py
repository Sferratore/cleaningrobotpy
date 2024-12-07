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



