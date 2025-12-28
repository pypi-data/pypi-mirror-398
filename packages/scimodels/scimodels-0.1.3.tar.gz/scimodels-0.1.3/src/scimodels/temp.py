import os
import time

_temp_dir = ".scimodels.tmp/"

def set_temp_dir(dir: str) -> None:
    global _temp_dir
    _temp_dir = dir

def get_temp_dir() -> str:
    if os.path.isabs(_temp_dir):
        return _temp_dir
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, _temp_dir)

def clear_temp_dir() -> None:
    temp_dir = get_temp_dir()

    if not os.path.isdir(temp_dir):
        return None
    
    age_limit = 86400 # 1 day
    now = time.time()

    failed_deletes = []

    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)

        if os.path.isfile(file_path):
            file_mtime = os.path.getmtime(file_path)
            if now - file_mtime > age_limit:
                try:
                    os.remove(file_path)
                except:
                    failed_deletes.append(filename)
    
    failed_count = len(failed_deletes)

    if failed_count > 0:
        plural = "" if failed_count == 1 else "s"
        file_list = ', '.join(failed_deletes[:4])
        if failed_count > 1:
            more_warning = f" and {failed_count - 4} more"
        else:
            more_warning = ""
        print(f"SciModels WARNING: Failed to delete expired file{plural}: {file_list}{more_warning}.")