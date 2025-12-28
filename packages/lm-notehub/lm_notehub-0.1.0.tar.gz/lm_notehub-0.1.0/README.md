# Notehub

Using Github issues as general notes.

# On Windows:

- Install the python.org edition of Python3.x, stay away from MS Store
- Installer should add to the PATH:
```
C:\Users\lmatheson4\AppData\Local\Programs\Python\Python313\Scripts
C:\Users\lmatheson4\AppData\Local\Programs\Python\Python313
C:\Users\lmatheson4\AppData\Local\Programs\Python\Launcher
```
- Installing notehub in "edit mode" allows for convenient development:
```
c:\Projects\notehub> python -m pip install -e .
- Don't listen to LLMs that say to use --user.  On Windows, --user puts stuff in AppData\Roaming
- instead of AppData\Local, but since you do actually own the latter no reason to use --user
```
- Use GH_ENTERPRISE_TOKEN_2 env within the corp wall, put in the Windows env.

