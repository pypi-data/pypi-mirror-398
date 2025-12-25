from AuthBarn import *

test = Action(enable_logging=True,dev_mode=True)

print(test.log("critical","message"))