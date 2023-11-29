# Feedback data converter

Converts feedback data that has been collected from courses.mooc.fi exercises to an Excel file.

## Usage

1. Download the program
   - Download the program from the `releases` section on the right side of this page.
2. Create a folder for the program
   - Create a new empty folder where you'll place the program. The program, the input files and the output files will be placed in this folder.
3. Running the program
  - 3.1. If you use a computer that does not allow you to run scripts, follow these instructions (else go to step 3.2.):
     - Go to vdi.helsinki.fi
     - Select the HTML / browser version (right side)
     - Log in with your username (8 characters) and password
     - Select Cubbli Linux
     - Find the folder where you saved the program
  - 3.2. Run the program
    - Double click the feedback-data-converter icon to run the program. This creates the configuration file `config.yml` in the same folder.
     - If you're running Linux, you'll need to allow executing the file as a program. (Right click the file, select Properties, go to Permissions tab and check the "Allow executing file as program" checkbox.)
4. Edit the configuration file `config.yml`
   - Right click the `config.yml` file -> `Open with` -> `Text Editor`
   - As show in the template, fill in `chapter_number` and `exercise_id` for each feedback exercise you want to include in the report. How to find the `exercise_id`? Open the course material in admin view → go to Exercises tab → click the name of the exercise → copy the string between exercises/ and /submissions, for example: 91fdaef8-9519-5a02-8f5f-53ba98xxxxx
6. Export exercise tasks and submissions from courses.mooc.fi
   - Open course material in admin mode -> Overview -> scroll down -> Click `Export submissions (exercise tasks) as CSV` and `Export exercise-tasks as CSV`
   - Place the downloaded CSV files to the folder called `data`.
7. Run the program (double click feedback-data-converter icon). The output file will be placed in a folder called `output`.

If you need to repeat the the process at a later date, with new data, simply repeat steps 6 and 7.

