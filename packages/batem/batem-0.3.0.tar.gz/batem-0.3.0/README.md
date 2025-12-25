# BATEM Tutorial

Welcome to the BATEM tutorial. This guide will help you learn about different aspects of energy management through hands-on exercises using Python and Jupyter notebooks.

## Overview

This tutorial consists of:
- Interactive Jupyter notebooks (named `notebookx_XXX.ipynb`)
- Lecture slides (named `slidesx_XXX.pdf`)


## Getting Started

Access the [MyBinder project](https://shorturl.at/dISF1) to start the tutorial.

Depending on your internet connection, you may have to wait a few minutes to start the tutorial.

**Important:**

- If you are unable to access the MyBinder environment, you can download the project files and run the notebooks locally.
- To do this, you need to go through the following steps:

### Local Installation Guide

1. **Install Python**
   - Download Python from [python.org](https://www.python.org/downloads/)
   - Choose the latest Python 3.x version
   - During installation, make sure to check "Add Python to PATH"
   - Verify installation by opening a terminal and typing (PowerShell in Windows, Terminal in macOS/Linux):
     ```bash
     python --version
     ```

2. **Install Visual Studio Code**
   - Download VS Code from [code.visualstudio.com](https://code.visualstudio.com/)
   - Install VS Code following the default installation steps
   - Open VS Code and install the following extensions:
     - "Python" by Microsoft
     - "Jupyter" by Microsoft

3. **Set up the Python Environment**
   - Open a terminal in VS Code (Terminal -> New Terminal)
   - Create a new virtual environment:
     ```bash
     python -m venv venv
     ```
   - Activate the virtual environment:
     - On Windows:
       ```bash
       .\venv\Scripts\activate
       ```
     - On macOS/Linux:
       ```bash
       source venv/bin/activate
       ```
   - Install required packages:
     ```bash
     pip install -r requirements.txt
     ```

4. **Run the Notebooks**
   - Open the project folder in VS Code
   - Open any .ipynb file
   - Select the Python interpreter (venv) when prompted
   - Follow the notebook

## Working with MyBinder

The MyBinder window should look like this:

<img src="figs/tutorial_binder_window.png" width="100%">

There are three main instruments to work with:
- The project files, accesible from the left panel (**Project Structure**)
- The command bar, at the top of the window (**Command Bar**)
- The working area, in the middle of the window (**Working window**)


## Following the tutorial

We recommend to follow the tutorial in the following order:

- Go thorugh the slides for a subject first (**slidesXX_XXX.md**)
- Open the corresponding notebook (**notebookXX_XXX.ipynb**)
   - Solve the exercises in the notebook by writing your replies in a separate document with the references to the questions and exercises.
   - You can check the slides to get the information you need to solve the exercises
- After finishing the exercises on a notebook, upload the responses to the course platform.


## Working with Notebooks

To open any notebook, double-click the corsponding .ipynb file.

### Notebook Basics

Notebooks contain two types of cells, as described bellow:

<img src="figs/tutorial_cell_types.png" width="100%">

1. **Text Cells** (for reading and writing):
   - Double-click to edit
   - Press **'Shift+Enter'** to execute the cell and display the text
   - Press **'Ctrl+S'** to save the notebook

2. **Code Cells** (for running Python):
   - Click the **Run** (▶️) button to run the cell
   - Alternatively, use the **"Restart and run all"** (▶️▶️) button in the top menu to run all the cells in the notebook


#### Notebooks in VS Code

If you are using VS Code and work with the notebooks locally on your machine, your notebook looks like this:

<img src="figs/tutorial_vs_code.png" width="100%">

To run a cell, you can either:
- Click the **Run** (▶️) button
- Use the **'Shift+Enter'** shortcut

To run all the cells in the notebook, you can either:
- Click the **"Restart"** button in the top menu
- Click the **Run All** button in the top menu



### Working with Plots

The interactive plots typically show evolution of parmaeters (such as power consumption) over time:

<img src="figs/tutorial_plots.png" width="100%">

- **View Specific Legend Item (for example an appliance)**: Double-click items in the legend
- **Zoom In**: Click and drag a rectangle on the plot
- **Zoom Out**: Click "Autoscale" in the top-right corner of the plot
- **View Details**: Hover over lines to see line-specific information

For example, hovering over a line in the power consumption plot will show the weather temperature in function of the time.


## Evaluation 

You will be evaluated based on the answers you provide to the questions and exercises in the notebooks.

**We strongly recommend you to put your answers on a separate document (word, pdf, txt, etc.) and provide clear references to the question numbers.**

After you have your document ready, you can upload it to the course platform.
 
**Example:**

In the notebook:
*Section I. Sun*
*Question 1. Calculated solar radiations vs measurements*
*Section I., Question 1: (your answer here)*

In the separate document:
*Section I., Question 1: (your answer here)*





