"""Task scheduling and automation runner."""

import argparse
import time
import schedule
from typing import Callable, Dict, List, Optional
from datetime import datetime
from .logger import setup_logger
from .config import Config

logger = setup_logger("TaskScheduler", level=Config.LOG_LEVEL)


class TaskScheduler:
    """Schedule and run automated tasks."""

    def __init__(self):
        """Initialize task scheduler."""
        self.tasks: Dict[str, Dict] = {}
        self.running = False

    def add_task(
        self,
        name: str,
        func: Callable,
        interval: str,
        interval_type: str = "minutes",
        args: tuple = (),
        kwargs: dict = None
    ) -> None:
        """Add task to scheduler.
        
        Args:
            name: Task name
            func: Function to execute
            interval: Interval value (e.g., '10', 'monday')
            interval_type: Type (seconds, minutes, hours, days, weeks, monday-sunday)
            args: Function positional arguments
            kwargs: Function keyword arguments
        """
        if kwargs is None:
            kwargs = {}
        
        job = None
        
        if interval_type == "seconds":
            job = schedule.every(int(interval)).seconds
        elif interval_type == "minutes":
            job = schedule.every(int(interval)).minutes
        elif interval_type == "hours":
            job = schedule.every(int(interval)).hours
        elif interval_type == "days":
            job = schedule.every(int(interval)).days
        elif interval_type == "weeks":
            job = schedule.every(int(interval)).weeks
        elif interval_type in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            job = getattr(schedule.every(), interval_type).at(interval)
        else:
            logger.error(f"Invalid interval type: {interval_type}")
            return
        
        job.do(func, *args, **kwargs)
        
        self.tasks[name] = {
            "func": func,
            "interval": interval,
            "interval_type": interval_type,
            "job": job,
            "last_run": None,
        }
        
        logger.info(f"Added task '{name}' - runs every {interval} {interval_type}")

    def remove_task(self, name: str) -> bool:
        """Remove task from scheduler.
        
        Args:
            name: Task name
            
        Returns:
            True if removed
        """
        if name in self.tasks:
            schedule.cancel_job(self.tasks[name]["job"])
            del self.tasks[name]
            logger.info(f"Removed task '{name}'")
            return True
        logger.warning(f"Task '{name}' not found")
        return False

    def list_tasks(self) -> List[Dict]:
        """List all scheduled tasks.
        
        Returns:
            List of task info dicts
        """
        return [
            {
                "name": name,
                "interval": task["interval"],
                "interval_type": task["interval_type"],
                "last_run": task["last_run"],
            }
            for name, task in self.tasks.items()
        ]

    def run_pending(self) -> None:
        """Run pending scheduled tasks."""
        schedule.run_pending()
        
        # Update last run times
        for name, task in self.tasks.items():
            if task["job"].last_run:
                task["last_run"] = task["job"].last_run

    def run_forever(
        self,
        check_interval: int = 1
    ) -> None:
        """Run scheduler loop forever.
        
        Args:
            check_interval: Seconds between schedule checks
        """
        self.running = True
        logger.info("Starting scheduler loop")
        
        try:
            while self.running:
                self.run_pending()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        finally:
            self.running = False

    def stop(self) -> None:
        """Stop scheduler loop."""
        self.running = False
        logger.info("Scheduler stopped")

    def run_task_now(self, name: str) -> bool:
        """Run specific task immediately.
        
        Args:
            name: Task name
            
        Returns:
            True if executed
        """
        if name in self.tasks:
            task = self.tasks[name]
            try:
                task["func"]()
                task["last_run"] = datetime.now()
                logger.info(f"Executed task '{name}'")
                return True
            except Exception as e:
                logger.error(f"Task '{name}' failed: {e}")
                return False
        logger.warning(f"Task '{name}' not found")
        return False


def example_task(message: str = "Task executed") -> None:
    """Example task function."""
    print(f"[{datetime.now()}] {message}")


def main() -> None:
    """CLI for task scheduler."""
    parser = argparse.ArgumentParser(description="Task scheduler utility")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo with example tasks"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        scheduler = TaskScheduler()
        
        # Add example tasks
        scheduler.add_task(
            "task1",
            example_task,
            "10",
            "seconds",
            args=("Task 1 running every 10 seconds",)
        )
        
        scheduler.add_task(
            "task2",
            example_task,
            "1",
            "minutes",
            args=("Task 2 running every minute",)
        )
        
        logger.info("Demo mode - Press Ctrl+C to stop")
        logger.info(f"Scheduled tasks: {scheduler.list_tasks()}")
        
        scheduler.run_forever()
    else:
        print("Use --demo to run example scheduler")
        print("Import TaskScheduler class to use programmatically")


if __name__ == "__main__":
    main()