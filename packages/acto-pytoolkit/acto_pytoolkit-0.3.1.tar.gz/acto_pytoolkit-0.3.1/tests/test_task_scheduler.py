"""Tests for the task_scheduler module."""
import time
import unittest
from unittest.mock import Mock

from pytoolkit.task_scheduler import TaskScheduler, ScheduledTask


class TestTaskScheduler(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.scheduler = TaskScheduler(tick=0.1)

    def tearDown(self):
        """Clean up after tests."""
        self.scheduler.stop()

    def test_add_and_execute_task(self):
        """Test adding and executing a scheduled task."""
        mock_func = Mock()
        
        self.scheduler.add_task("test_task", interval=0.2, function=mock_func)
        self.scheduler.start()
        
        # Wait for task to execute at least once
        time.sleep(0.4)
        
        self.assertGreaterEqual(mock_func.call_count, 1)

    def test_task_with_arguments(self):
        """Test scheduled task with arguments."""
        mock_func = Mock()
        
        self.scheduler.add_task(
            "task_with_args",
            0.2,
            mock_func,
            "arg1",
            "arg2",
            key="value"
        )
        self.scheduler.start()
        
        time.sleep(0.3)
        
        mock_func.assert_called()
        # Check that arguments were passed correctly
        call_args = mock_func.call_args_list[0]
        self.assertEqual(call_args[0], ("arg1", "arg2"))
        self.assertEqual(call_args[1], {"key": "value"})

    def test_remove_task(self):
        """Test removing a scheduled task."""
        mock_func = Mock()
        
        self.scheduler.add_task("removable_task", interval=0.1, function=mock_func)
        self.scheduler.start()
        
        time.sleep(0.15)
        call_count_before = mock_func.call_count
        
        self.scheduler.remove_task("removable_task")
        time.sleep(0.3)
        
        # Call count should not increase after removal
        self.assertEqual(mock_func.call_count, call_count_before)

    def test_replace_task(self):
        """Test replacing an existing task."""
        mock_func1 = Mock()
        mock_func2 = Mock()
        
        self.scheduler.add_task("replaceable", interval=0.2, function=mock_func1)
        self.scheduler.add_task("replaceable", interval=0.2, function=mock_func2)
        self.scheduler.start()
        
        time.sleep(0.3)
        
        # Only the second function should be called
        self.assertEqual(mock_func1.call_count, 0)
        self.assertGreaterEqual(mock_func2.call_count, 1)

    def test_task_exception_handling(self):
        """Test that exceptions in tasks don't stop the scheduler."""
        failing_func = Mock(side_effect=ValueError("Task error"))
        working_func = Mock()
        
        self.scheduler.add_task("failing", interval=0.1, function=failing_func)
        self.scheduler.add_task("working", interval=0.1, function=working_func)
        self.scheduler.start()
        
        time.sleep(0.3)
        
        # Both tasks should have been attempted despite the failure
        self.assertGreater(failing_func.call_count, 0)
        self.assertGreater(working_func.call_count, 0)

    def test_scheduled_task_cancel(self):
        """Test cancelling a ScheduledTask."""
        task = ScheduledTask(interval=1.0, function=lambda: None)
        
        self.assertFalse(task._cancelled)
        task.cancel()
        self.assertTrue(task._cancelled)

    def test_stop_scheduler(self):
        """Test stopping the scheduler."""
        mock_func = Mock()
        
        self.scheduler.add_task("test", interval=0.1, function=mock_func)
        self.scheduler.start()
        
        time.sleep(0.15)
        call_count = mock_func.call_count
        
        self.scheduler.stop()
        time.sleep(0.3)
        
        # No new calls after stop
        self.assertEqual(mock_func.call_count, call_count)

    def test_start_already_running(self):
        """Test starting an already running scheduler."""
        self.scheduler.start()
        self.assertTrue(self.scheduler._thread.is_alive())
        
        # Starting again should not create a new thread
        self.scheduler.start()
        self.assertTrue(self.scheduler._thread.is_alive())


if __name__ == "__main__":
    unittest.main()

