from Queue import Queue


class Task(object):
    def __init__(self, target):
        self.target = target()
        self.target.next()

    def run(self):
        self.target.send(None)


class Scheduler(object):
    def __init__(self):
        self.task_queue = Queue()

    def new_task(self, target):
        task = Task(target)
        self.task_queue.put(task)

    def main_loop(self):
        while self.task_queue:
            task = self.task_queue.get(block=False)

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
