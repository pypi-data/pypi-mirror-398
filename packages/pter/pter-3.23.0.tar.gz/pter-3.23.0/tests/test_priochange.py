"""Test cases for the increase_priority and decrease_priority functions"""
import unittest

from pytodotxt import Task
from pter import utils


class TestChangePriorities(unittest.TestCase):
    def test_increase_none(self):
        task = Task('Task without priority')
        utils.increase_priority(task)

        self.assertEqual(str(task), "(Z) Task without priority")

    def test_increase_normal(self):
        task = Task('(C) Task with some priority')
        utils.increase_priority(task)

        self.assertEqual(str(task), "(B) Task with some priority")

    def test_increase_maxed(self):
        task = Task('(A) Task with the highest priority')
        utils.increase_priority(task)

        self.assertEqual(str(task), "(A) Task with the highest priority")

    def test_decrease_none(self):
        task = Task('Task without priority')
        utils.decrease_priority(task)

        self.assertEqual(str(task), "Task without priority")

    def test_decrease_normal(self):
        task = Task('(C) Task with some priority')
        utils.decrease_priority(task)

        self.assertEqual(str(task), "(D) Task with some priority")

    def test_decrease_maxed(self):
        task = Task('(Z) Task with the lowest priority')
        utils.decrease_priority(task)

        self.assertEqual(str(task), "Task with the lowest priority")

    def test_change_completed_tasks(self):
        task = Task('x Completed task pri:C')
        utils.increase_priority(task)
        self.assertIs(task.priority, None)
        self.assertEqual(str(task), "x Completed task pri:C")

        utils.decrease_priority(task)
        self.assertEqual(str(task), "x Completed task pri:C")
