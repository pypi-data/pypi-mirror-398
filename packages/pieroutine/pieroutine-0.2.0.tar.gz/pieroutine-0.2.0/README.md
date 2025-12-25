# Description of the project
In this project our purpose is that implement a mechanism like goroutine.
This mechanism is already implemented in threading or multiprocessing libraries , but we want to find out that 
what actually happen when we want to manage processes and waiting for them.


# Sections
1. process.py : In this file the functions that you need to run your tasks in concurrent placed.
you can run your tasks with process or a pool of process (for using wait group functionality you'r not forced to use this functions).

2. wait_group.py : In this file a module implemented that you can use it for controlling your concurrent tasks.
for example you want to run multiple process in background and you need to know when exactly they done, so you use wait group (like waitGroup() in go).
you can use `.join()` too btw.


# What i learned
1. understanding difference of process and thread
2. understanding and using shared variables
3. using un-usual data structure in this environment like `Queue()`