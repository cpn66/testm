from threading import Thread
import time

class Streams:
    def __init__(self, max_cpu):
        self.process = 0
        self.streams = dict()
        self.max_cpu = max_cpu

    def add(self, type_process, function, args):
        if self.process < self.max_cpu:
            t = Thread(target=function, args=args, daemon=True)
            t.start()
            if type_process not in self.streams:
                self.streams[type_process] = list()
            self.streams[type_process].append(t)
            self.process += 1
            # print(f"New process: {self.process}")
            return True
        else:
            if type_process not in self.streams:
                self.streams[type_process] = list()
            if len(self.streams[type_process]) > 0:
                t = self.streams[type_process].pop(0)
                t.join()
                self.process -= 1
                # print(f"End process: {self.process}")
            else:
                time.sleep(0.1)
            self.add(type_process, function, args)

    def end(self, type_process):
        if type_process not in self.streams:
            self.streams[type_process] = list()
        if len(self.streams[type_process]) > 0:
            t = self.streams[type_process].pop(0)
            t.join()
            self.process -= 1
            # print(f"End process: {self.process}")
            self.end(type_process)
        else:
            return True

    def del_process(self, type_process):
        if type_process not in self.streams:
            del self.streams[type_process]
        return True
