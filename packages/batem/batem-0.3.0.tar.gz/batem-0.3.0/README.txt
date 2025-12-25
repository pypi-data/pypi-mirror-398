Download the batem project and unzip it, or clone the project with:
    
# Getting the code

git clone https://gricad-gitlab.univ-grenoble-alpes.fr/ploixs/batem.git 

# Getting the required libraries

Launch a terminal in "Visual Studio code", the "Powershell" (Windows) or the "Terminal" (MacOS, Linux) application on your Operating System

Go inside the core folder:

cd <PATH_TO_CORE>

pip install -r requirements.txt

# some libraries might to install properly using the `requirements.txt` file

# Getting data

- If you are at ENSE3, modify the `setup.ini` file at code root folder by commenting (with a ';' in front) as follows:

[folders]
;data = ./../data/
data = //FILE-V04.e3.local/Pedagogie/buildingenergy/data/
results = ./results/
linreg = linreg/
sliding = sliding/
figures = figures/ 
[sizes]
width = 8
height = 8
[databases]
irise = irise38.sqlite3

- Otherwise, keep it as it is:

[folders]
data = ./../data/
;data = //FILE-V04.e3.local/Pedagogie/buildingenergy/data/
results = ./results/
linreg = linreg/
sliding = sliding/
figures = figures/ 
[sizes]
width = 8
height = 8
[databases]
irise = irise38.sqlite3

but download the data from https://cloud.univ-grenoble-alpes.fr/s/XzJnkg3NQLYskg5

Unzip and move the data at the same level than the root folder for code

- wherever you are, your file system should look like:

/your_containing_folder
    /data
    /buildingenergy
        /buildingenergy
        /doc
        /ecommunity
        /img
        /results
        /sites
        /slides
        notebook...
        ...
        requirements.txt
        setup.ini

        ________________________

________________________
Let's remind the buildingenergy's main features:
- automatic retrieval of historical weather data from anywhere in the world, as well as skyline-type solar masks
- calculation of solar gain on any surface, taking into account near, medium and far masks + PV production calculation
- parametric analysis of a typical house (lambda) immersed in a given environment, to get a quick idea of the design axes to be favored (but this is by no means a validation, as the inertia is fixed on an average case, as the following point shows)
- multi-zone dynamic energy simulation, taking into account air quality (CO2 concentration), with control and calculation of resulting performance, and taking into account the presence + design of curves (temperature setpoints, occupancy profiles). Compared with Pléiades, the descriptions are faster and it's more control/command-oriented, but although the results are very close in fine, Pléiades takes more elements into account: solar radiation on external walls and shading, illuminance (but not air quality). BuildingEnergy can be seen as a relatively early-stage tool, but does not dispense with validation via Pléiades, which is certified.
- model calibration for energy audits
- and many other tools
________________________
The buildingenergy installation procedure is as follows:

install Python + Visual Studio Code:

	https://youtu.be/cUAK4x_7thA?si=j6MN5pyvFkL94mQz

install Git:

	https://youtu.be/JgOs70Y7jew?si=36_H_6icnVIIGrU8

then go to  https://gricad-gitlab.univ-grenoble-alpes.fr/ploixs/buildingenergy and click on code / Open in IDE / Visual Studio Code (HTTPS)  

# Get the BuildingEnergy required libraries

Launch a terminal in "Visual Studio code" (Terminal toolbar), or "Powershell" on Windows / "Terminal" on MacOS, Linux

Go to the buildingenergy root directory, which contains another buildingenergy folder, the site directory, and more:
    cd <PATH_TO_buildingenergy>
    pip install -r requirements.txt

Some libraries may not install correctly using the `requirements.txt` file: you need to install them manually with:
pip install <missing_python library>

- If you are at ENSE3, modify the `setup.ini` file at code root folder by commenting (with a ';' in front) as follows:

[folders]
;data = ./../data/
data = //FILE-V04.e3.local/Pedagogie/buildingenergy/data/
results = ./results/
linreg = linreg/
sliding = sliding/
figures = figures/ 
properties = ./
[sizes]
width = 8
height = 8
[databases]
irise = irise38.sqlite3

- Otherwise, keep it as it is:

[folders]
data = ./../data/
;data = //FILE-V04.e3.local/Pedagogie/buildingenergy/data/
results = ./results/
linreg = linreg/
sliding = sliding/
figures = figures/ 
properties = ./
[sizes]
width = 8
height = 8
[databases]
irise = irise38.sqlite3

- your file system should look like this :

    /your_root_folder
        /buildingenergy
        /doc
        /ecommunity
        /img
        /results
        /sites
        /slides
        notebook...
        ...
        requirements.txt
        setup.ini

If you can't run a code under windows because the system doesn't see the Python files even though they exist, create a PYTHONPATH environment variable with the value "." (without quotes) from Control Panel / System
________________________
The code is constantly evolving. To update it, type in the Terminal window :
    git pull
If you've made changes to certain files, it won't want to update the code. In this case, you need to copy the modified files and then return to the repository state with :
    git reset --hard 
________________________
The basic concepts of thermic are summarized in:
	https://cghiaus.github.io/dm4bem_book/intro.html
You'll also find a wealth of documents in the project's doc/ directory.You'll also find a wealth of documents in the project's doc/ directory.

A user manual of the buildingenergy project used for simulation with control can be found in the doc folder of the project: it is named control_building.md, written in markdown format (use the All-In-One Markdown extension in Visual Studio Code, or an external markdown editor).