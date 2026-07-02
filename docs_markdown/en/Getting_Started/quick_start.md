# Contributor Start Guide

## Contribution Terms

By contributing to this project, you agree that your contributions will be licensed under the Apache License, Version 2.0.
You acknowledge that you will not receive payment or compensation for your contributions.

## Prerequisites

- Python 3.12.3
- pip

## Get BLADE

1. Click on "Clone or download", and then "Download Zip".
2. Unzip the repo anywhere.
3. Navigate to the folder that contains `setup.py` and install the repository using:

   ```bash
   pip install .
   ```

   Anytime you make changes to the files in the project folder, you need to reinstall the package using:

   ```bash
   pip install .
   ```

   Alternatively, use:

   ```bash
   pip install -e .
   ```

   to install the package in editable mode. After doing this you can change the code without needing to continue to install it.

4. `gymnasium` is a dependency for users who want to use BLADE as a Gym environment. In this case, use:

   ```bash
   pip install .[gym]
   ```

   or:

   ```bash
   pip install -e .[gym]
   ```

## Run a Demo

1. Run the provided demo in `scripts/simple_demo/demo.py`.
2. The demo will output a scenario file that can be viewed using the frontend GUI.

## Setting up the Client

1. Click on "Clone or download", and then "Download Zip".
2. Unzip the repo anywhere.
3. Navigate to the `client` folder and install the client using:

   ```bash
   npm install
   ```

   To run the client without a server:

   ```bash
   npm run standalone
   ```
