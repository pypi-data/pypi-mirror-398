from time import sleep, time
beginning = time()
start_time = 0
end_time = 0
show =  0
laps = []
def wait(millis):
    """
    Pause the program for the given milliseconds
    """
    sleep(millis / 1000)

class stopwatch:
    def start():
        """
        Start the stopwatch
        """
        global start_time
        start_time = time()
    def stop():
        """
        Stop the stopwatch
        """
        global end_time, show
        end_time = time()
        show = end_time - start_time
    def returnlaps():
        """
        Return all the laps in list format
        """
        return laps
    def returntime():
        """
        Return the time the stopwatch has run
        """
        return show
    def resume():
        """
        Resume the stopwatch after it has been stopped
        """
        start = 0
    def lap():
        """
        Make a lap
        """
        lap_time = time()
        laps.append(lap_time - start_time)
def from_start():
    """
    Return the time elapsed since the module was imported
    """
    return time() - beginning
