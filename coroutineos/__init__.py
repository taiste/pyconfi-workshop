from uuid import uuid4
from Queue import Queue, Empty


class Task(object):
    def __init__(self, target):
        self.id = uuid4()
        self.target = target()
        self.target.next()

    def run(self):
        self.target.send(None)


class Scheduler(object):
    def __init__(self):
        self.task_queue = Queue()
        self.tasks = {}

    def new_task(self, target):
        task = Task(target)
        self.tasks[task.id] = task
        self.task_queue.put(task)

    def main_loop(self):
        while self.task_queue:
            try:
                task = self.task_queue.get(block=False)
            except Empty:
                print 'No more tasks, exiting!'
                break

            try:
                task.run()
            except StopIteration:
                # Do not schedule if the task is done
                continue
            self.task_queue.put(task)


if __name__ == '__main__':
    def task1():
        for _ in range(20):
            print 'Task #1'
            yield

    def task2():
        for _ in range(10):
            print 'Task #2'
            yield

    scheduler = Scheduler()
    scheduler.new_task(task1)
    scheduler.new_task(task2)
    scheduler.main_loop()
