from accelerate.state import PartialState
state = PartialState()

@state.on_local_main_process
def local_print(s):
    print(s)

