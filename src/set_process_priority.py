import os
import psutil


def set_process_priority():
    p = psutil.Process(os.getpid())
    try:
        p.nice(psutil.HIGH_PRIORITY_CLASS)  # For Windows
    except AttributeError:
        p.nice(-10)  # For Unix systems
    except Exception as e:
        print(f'ERROR: {e}')
        print('Could not set process priority. Continuing execution...')
