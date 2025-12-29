import os
import stat

def validate():
    if not os.path.exists("script.sh"):
        return False, "script.sh does not exist."

    st = os.stat("script.sh").st_mode

    owner = st & stat.S_IRWXU
    group = st & stat.S_IRWXG
    other = st & stat.S_IRWXO

    if owner == stat.S_IRWXU and group == 0 and other == 0:
        return True, "Correct permissions!"
    else:
        return False, f"Permissions incorrect. Expected 700."

