from .courses import courses

def total_duration():

    return sum(i.duration for i in courses)
