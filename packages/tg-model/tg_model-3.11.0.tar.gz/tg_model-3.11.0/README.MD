# TextGrid Import Modeller

## Whats the aim?

This project focuses on attemps for a simple import of text corpora (encoded in XML/TEI) to [TextGrid Repository](https://textgrid.de) by modeling the required metadata file structure.

> __NOTE__:
    !This is work in progress!
        _
    Feedback on anything that does not work or needs to be modified is welcome!!!

## Installation

The source code is maintained here: https://gitlab.gwdg.de/textplus/textplus-io/textgrid_import_modelling

Clone the project:

```bash
git clone https://@gitlab.gwdg.de/textplus/textplus-io/textgrid_import_modelling.git -o {{ your/project/path/name }}
```

It is recommended to install the project in a local virtual python environment and therefore the necessary steps are basically described:

### Version 1 (recommended)

Simply create it within tg_model. Naming in `venv` while setting the prompt to the name of the current directory:

```bash
cd {{ your/project/path/name }}
python3 -m venv venv/ --prompt "$(pwd | grep -o "[^/]*$")"
. venv/bin/activate
pip install -e .
```

### Version 2

Create it at your favored path:

```bash
# create new virtual environment
python3 -m venv {path/to/your/virtEnv}
# activate virtual environment
. {path/to/your/virtEnv}/bin/activate
# install this project
pip install -e {{ your/project/path/name }}
```

## What can be done? (so far)

- [Discover Synergies](#discover)
- [Build metadata structure needed for TextGrid import](#build)

<span id="build"></span>
### Build metadata structure needed for TextGrid import

#### 1. init a major config...defining the project and subprojects

You have different options to set the path(s) to your input data.

##### "Manual" option

Simply set the path to the directory of your TEI files. You can also set a list of paths, seperated by comma.

**single directory**

```bash
tg_configs -n {projectname} project -i {path/to/tei/directory/containing/files}
```

**multiple directory**

```bash
tg_configs -n {projectname} project -i {1st/path/to/tei/files},{2nd/path/to/tei/files},{3rd/path/to/tei/files}
```

##### "Automatic" option

When you have many sub-directories or sub-projects you can also let tg_model automatically find the directories containing TEI files by setting the basic path containing all sub-projects + the name of the directory, that contains TEI files. The name of that directory has to be identical for all directories!

```bash
tg_configs -n {projectname} project -s {path/to/base/directory} -t {name/of/directory/containing/tei/files}
```
#### 2. init a collection config

```bash
tg_configs -n {projectname} collection
```

This creates the final config, which is needed to build the TextGrid metadata structure.

What the code does:

- trying to find proposed xpaths inside of all given XML/TEI files
- if it finds a node by a proposed xpath more time than a defined `hit_rate` (defined in `project.yaml`), than this xpath is added to the the "collection config"

**Mandatory**

All attributes for "rights_holder" & "title" have to be filled out, as these attributes get validated (only for existance) before the code models the structure.


4. init a collection config

Finally one can build the TextGrid metadata structure

```bash
tg_model -n {projectname} build-collection
```

This puts all the files in `./output`, but this can be manually defined `tg_model build-collection --help`

![overview of whole workflow](./docs/workflow.drawio.png)

## Exemplary executions

```bash
mkdir /tmp/FluffyModelling
cd /tmp/FluffyModelling
```

### CoNSSA

```bash
# get corpus
git clone https://github.com/cligs/conssa.git conssa

# initialize all configs
tg_configs -n CoNSSA all -s conssa -t master
```

Now you can find the project config at: `/tmp/FluffyModelling/projects/CoNSSA` and the related subproject at: `/tmp/FluffyModelling/projects/conssa_master_master` containing configs for collection.

For CoNSSA, there is no need for manual editing of the configs, so you can go on and create the meta data files:

```bash
tg_model -n CoNSSA build-collection
```

Afterwards, you can find them at: `/tmp/FluffyModelling/projects/CoNSSA/conssa_master_master/result`

### ELTeC-fra

```bash
# get corpus
git clone https://github.com/COST-ELTeC/ELTeC-fra eltec-fra

# initialize all configs
tg_configs -n ELTeC-fra all -s eltec-fra -t level1
```

Now you can find the project config at: `/tmp/FluffyModelling/projects/ELTeC-fra`

ELTeC needs modifications at the collection config:

```bash
nano /tmp/FluffyModelling/projects/ELTeC-fra/FluffyModelling_eltec-fra_level1/collection.yaml
# --> set all attributes of 'rights_holder'

# create the meta data files
tg_model -n ELTeC-fra build-collection
```

Afterwards, you can find them at: `/tmp/FluffyModelling/projects/ELTeC-fra/tgm_output`


### Multi-project examples

#### textbox

```bash
git clone https://github.com/cligs/textbox

tg_configs -n textbox all -s textbox -t tei

tg_model -n textbox build-collection
```

#### ELTeC

```bash
tg_configs -n ELTeC all -s ELTeC -t level1

tg_model -n ELTeC build-collection
```

## 4Developer

This project is built up in a very simple click-based setup. _(see ["python click"](https://click.palletsprojects.com/en/8.1.x/))_

All **commandline entry points** (e.g. `tg_model`, `tg_configs`, ...) are defined within the _`entry_points` section_ of [**`setup.py`**](setup.py).

### Contribution

Please use **separate branches** for your changes.
This will make it easier for us to review and merge your contributions.

Once you have made your changes, **add an entry to the [Changelog](Changelog)** at the end of the '# Latest features and bugfixes' section.
This will help us keep track of all the changes made to the project.

Finally, **create a merge request** to submit your changes.
This will allow us to review your changes and merge them into the main branch once they have been approved. Thank you for your contributions!


# [License](./LICENSE.txt)

While the specific **implementations** are located in [**`tg_model/cli.py`**](./tg_model/cli.py).

Copyright [2024] [TU Dresden | CIDS | ZIH]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
