import os
import yaml
import polars as pl
import json
from pprint import pprint
from collections import defaultdict
import xlsxwriter
from datetime import date
import numpy as np
import pdb
import sys

current_file_path = sys.executable
basename = os.path.basename(current_file_path)
if basename == "python.exe" or basename == "python" or basename == "python3":
    print("Running from source")
    current_file_path = __file__


def main():
    # Change pwd to the directory of this file

    abspath = os.path.abspath(current_file_path)
    dname = os.path.dirname(abspath)
    print(f"Changing working directory to {dname}")
    os.chdir(dname)

    # If config.yml does not exist, create it from the template
    if not os.path.exists("config.yml"):
        with open("config.yml", "w") as f:
            f.write(
                """feedback-exercises:
  - chapter_number: 1
    exercise_id: x
  - chapter_number: 2
    exercise_id: y
              """
            )
        print(
            "Created config.yml from template. Please edit the file and run the script again."
        )
        sys.exit(255)

    with open("config.yml", "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    print("Loaded config.yml")

    # Create the data folder if it does not exist
    if not os.path.exists("./data"):
        os.makedirs("./data")

    # Read the needed files from the ./data repository
    submission_files = []
    exercise_tasks_files = []
    datafiles = [
        f for f in os.listdir("./data/") if os.path.isfile(os.path.join("./data/", f))
    ]
    # filter out filenames that contain ".~lock."
    datafiles = [f for f in datafiles if ".~lock." not in f]

    for f in datafiles:
        [course_name, file_name] = f.split(" - ", 1)
        if "Submissions" in file_name:
            submission_files.append(f)
        elif "Exercise tasks" in file_name:
            exercise_tasks_files.append(f)

    # Sort the files by date, most recent first
    submission_files = sorted(
        submission_files, key=lambda x: (x.split(" ")[-1]), reverse=True
    )
    exercise_tasks_files = sorted(
        exercise_tasks_files, key=lambda x: (x.split(" ")[-1]), reverse=True
    )

    if len(submission_files) == 0:
        print(
            "No submission files found in ./data folder. Please download the data export and place the files in the ./data folder."
        )
        sys.exit(255)
    most_recent_submission_file = submission_files[0]

    if len(exercise_tasks_files) == 0:
        print(
            "No exercise tasks files found in ./data folder. Please download the data export and place the files in the ./data folder."
        )
        sys.exit(255)
    most_recent_exercisetasks_file = exercise_tasks_files[0]

    print(f'Using the file "{most_recent_submission_file}" as input for submissions.')
    print(
        f'Using the file "{most_recent_exercisetasks_file}" as input for exercise tasks.'
    )
    print()

    feedback_exercises = sorted(
        cfg["feedback-exercises"], key=lambda x: (x["chapter_number"]), reverse=False
    )

    df_submissions = pl.read_csv(
        f"./data/{most_recent_submission_file}",
        infer_schema_length=10000,
        try_parse_dates=True,
    )
    print(f"Found {len(df_submissions)} submissions in the file.")

    # One user may have submitted multiple times, we only want the most recent submission
    df_submissions = df_submissions.sort(by="created_at", descending=True)
    df_submissions = df_submissions.unique(
        subset=["user_id", "exercise_task_id"], maintain_order=True
    )

    print(
        f"After removing duplicates, there are {len(df_submissions)} submissions left."
    )

    print("")

    df_exercise_tasks = pl.read_csv(
        f"./data/{most_recent_exercisetasks_file}",
        infer_schema_length=10000,
        try_parse_dates=True,
    )

    # dict with default values
    res = defaultdict(lambda: defaultdict(dict))
    ex_submission_by_exercise_slide_submission_id = dict()

    for feedback_exercise in feedback_exercises:
        print(
            f"Parsing feedback for chapter {feedback_exercise['chapter_number']}, exercise {feedback_exercise['exercise_id']}."
        )
        # Select rows where the exercise id is the one we are looking for
        ex_df = df_submissions.filter(
            pl.col("exercise_id") == feedback_exercise["exercise_id"]
        )
        print(f"Found {len(ex_df)} submissions for this exercise.")
        for ex_submission in ex_df.rows(named=True):
            # Save the exercise submission to a dict so that it's easy to find the data later
            ex_submission_by_exercise_slide_submission_id[
                ex_submission["exercise_slide_submission_id"]
            ] = ex_submission

            exercise_task_id = ex_submission["exercise_task_id"]
            exercise_task = df_exercise_tasks.filter(
                pl.col("id") == exercise_task_id
            ).rows(named=True)[0]
            exercise_task_private_spec = json.loads(exercise_task["private_spec"])
            data_json = json.loads(ex_submission["data_json"])
            # parse the json
            # Assume the answer is either an essay or a scale
            for item_answer in data_json["itemAnswers"]:
                quiz_item_id = item_answer["quizItemId"]
                quiz_items_private_spec_array = exercise_task_private_spec["items"]
                quiz_item_private_spec = [
                    x for x in quiz_items_private_spec_array if x["id"] == quiz_item_id
                ][0]
                quiz_item_title = quiz_item_private_spec["title"]
                try:
                    if (
                        "textData" in item_answer
                        and item_answer["textData"] is not None
                    ):
                        # Essay
                        text_data = item_answer["textData"].strip()
                        # print(f"{quiz_item_title}: {text_data}")
                        res[feedback_exercise["chapter_number"]][
                            ex_submission["exercise_slide_submission_id"]
                        ]["Open feedback"] = text_data
                    else:
                        selected_option = item_answer["intData"]
                        if selected_option is None:
                            selected_option = int(item_answer["optionAnswers"][0])
                        # print(f"{quiz_item_title}: {selected_option}")
                        res[feedback_exercise["chapter_number"]][
                            ex_submission["exercise_slide_submission_id"]
                        ][quiz_item_title.strip()] = selected_option
                except Exception as e:
                    print("Error", e)
                    print("item_answer", item_answer)
                    raise e

    ### Writing the result
    # extract all keys from the nested dict
    all_keys = set()
    for chapter in res:
        for exercise_slide_submission_id in res[chapter]:
            for key in res[chapter][exercise_slide_submission_id]:
                all_keys.add(key)

    # Sort all keys except "Open feedback" should be last all_keys = sorted(all_keys)
    def sort_key(x):
        if x == "Open feedback":
            return f"zzzzzzzzzzzzzzzzzzzzzzz{x}"
        else:
            return x

    all_keys = sorted(all_keys, key=sort_key)
    print()
    print(f"Using questions: {all_keys}")
    print()

    current_timestamp_in_iso_format = date.today().isoformat()
    workbook = xlsxwriter.Workbook(
        f"./output/feedback_{current_timestamp_in_iso_format}.xlsx"
    )

    # create output folder if it does not exist
    if not os.path.exists("./output"):
        os.makedirs("./output")

    # Write an excel worksheet for each chapter
    for chapter in res:
        print(f"Writing chapter {chapter} to excel.")
        data = list()
        for exercise_slide_submission_id in res[chapter]:
            whole_submission = ex_submission_by_exercise_slide_submission_id[
                exercise_slide_submission_id
            ]
            row = [
                whole_submission["created_at"],
                whole_submission["user_id"],
                exercise_slide_submission_id,
            ]
            for key in all_keys:
                if key in res[chapter][exercise_slide_submission_id]:
                    row.append(res[chapter][exercise_slide_submission_id][key])
                else:
                    row.append("")
            # Add the average of all numbers in row to the end of the row
            all_numbers_in_row = [
                x for x in row[1:] if isinstance(x, int) or isinstance(x, float)
            ]
            if len(all_numbers_in_row) > 0:
                # Average
                row.append(np.mean(all_numbers_in_row))
                # Median
                row.append(np.median(all_numbers_in_row))
                # Standard deviation
                row.append(np.std(all_numbers_in_row))
            else:
                row.append("")
                row.append("")
                row.append("")
            data.append(row)

        schema = ["created_at", "user_id", "submission_id"]
        schema.extend(all_keys)
        schema.extend(["Mean", "Median", "Standard deviation"])
        df_chapter = pl.DataFrame(data, schema=schema).sort(
            by="created_at", descending=True
        )
        df_chapter.write_excel(
            workbook=workbook,
            worksheet=f"Chapter {chapter}",
            header_format={"bold": True, "text_wrap": True, "valign": "top"},
            row_heights={0: 200},
            column_widths={
                "created_at": 140,
                "submission_id": 270,
                "user_id": 270,
                "Open feedback": 600,
            },
        )

    workbook.close()


if __name__ == "__main__":
    main()
