import os

def validate():
    if not os.path.isdir("project"):
        return False, "Directory 'project' missing."

    notes = "project/notes.txt"
    if not os.path.exists(notes):
        return False, "notes.txt missing inside project."

    with open(notes) as f:
        if f.read().strip() == "DevOpsMind":
            return True, "Correct!"
        return False, "notes.txt content incorrect."

