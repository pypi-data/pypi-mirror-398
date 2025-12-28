
## 1. Setup Python and JupyterLab

If you're on Windows 11, open the `Terminal` app; if you're still running Windows 10, open `Windows PowerShell`.

Install uv with

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Next, make uv to play nice with SYSTRA firewall and point it to download packages from our repository

```powershell
setx UV_NATIVE_TLS true
```

Then restart the terminal.

Move to a directory of you liking, then create the jupyterlab python environment with

```powershell
uv init --python 3.12
uv add jupyterlab jupyter-lsp jupyterlab-lsp python-lsp-server[all]
```

> **NOTE**: as of today (2025-05-21) ifcopenshell doesn't support versions newer than 3.12, this is why we added `--python 3.12` option to `uv init`

verify it is working with

```powershell
uv run jupyter-lab
```

**NOTE**: every time you want to start jupyter lab, you need to be in the same directory!
But we can create a shortcut to always start jupyter the right way…
Paste the following code in the terminal (you might need to stop jupyterlab to reuse the terminal above)

```powershell
$workingDir = (Get-Item .).FullName
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\JupyterLab.lnk")
$shortcut.TargetPath = "$env:USERPROFILE\.local\bin\uv.exe"
$shortcut.Arguments = 'run jupyter-lab'
$shortcut.WorkingDirectory = $workingDir
$shortcut.IconLocation = "$workingDir\.venv\Lib\site-packages\jupyter_server\static\favicon.ico"
$shortcut.Save()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell)
```

If you don't trust the script, here's how to do it manually:

- Right click on your desktop -> New Shortcut
  ![[jupyter-shortcut-1.png]]
- In the input box, type `uv` and click `Next` or press enter
  ![[jupyter-shortcut-2.png]]
- Give it a name of you liking and click `Finish` or press enter
  ![[jupyter-shortcut-3.png]]
- right click on the shortcut and select `Properties`
  ![[jupyter-shortcut-4.png]]
- in `Target`, add `run jupyter-lab` at the end of the existing text
- in `Start in`, paste the full path of the directory you initialized above
- If you want, you can change the icon here
  ![[jupyter-shortcut-5.png]]

## 2. Installing packages with uv inside jupyter or from PS

To install new packages/libraries, run a cell with the `!uv add` and the package names, for example:

```jupyter
!uv add pandas openpyxl
```

these will be installed and also added to the `pyproject.toml` file, so that you can re-create the python/jupyterlab environment on another computer

> **TIP**: You can also run the `uv add` command (without the leading `!`) inside a terminal, provided you're in the directory of the environment

> **NOTE**: you can install packages from the systra repository if you have a gitlab.com account, create a personal access token and ask to be added to the `swsengineering` group.
> you need to set the `UV_INDEX_URL` environment variable:
>
> ```powershell
> setx UV_INDEX_URL https://__token__:<YOUR_TOKEN_HERE>@gitlab.com/api/v4/groups/9596324/-/packages/pypi/simple
> ```

## code completion

- go to `Settings` -> `Settings Editor` (or press ++ctrl+,++)
- in the `Search settings…` box type `completion`
- Under one of the `Code Completion` sections select `Enable autocompletion` and in the other select `Continuous hinting`

## 3. Develop configuration

While was cloned repository pyfrc with:
```powershell
$ git clone https://gitlab.com/luigi_paone/pyfrc.git
```

Go to jupyter folder created with 
```powershell
$ uv add <where is your pyfrc root folder>
```
