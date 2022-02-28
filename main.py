""" Login, get feedbacks, then find ratings from the last x number of passed and failed projects.
"""
import json
import configparser
from modules.udacity_browser import UdacityBrowser
from pprint import pprint
import pandas as pd
import os
import random

def add_to_metrics(metrics, feedback, is_passed, data_row=None):
    """ Update metrics and optionally data row with given feedback.

    Args:
        metrics(dict): The metrics dict.
        feedback(list): The feedback list from Udacity's student_feedbacks page
        (responses > feedback)
        is_passed(Boolean): True if the project meets specifications.
        data_row(pd.Series): A row from the data.csv file.
    """
    for f in feedback:
        if is_passed:
            metrics[f['key']]['passed'].append(int(f['rating']))
        else:
            metrics[f['key']]['failed'].append(int(f['rating']))
        if data_row is not None:
            data_row[f['key']] = int(f['rating'])

def calc_metrics(metrics, max_rating=5):
    """ Find the average score for each metric.
    """
    results = {}
    for k in metrics:
        total_meets = len(metrics[k]['passed']) * max_rating
        total_fails = len(metrics[k]['failed']) * max_rating
        avg_meets = sum(metrics[k]['passed']) / total_meets
        avg_fails = sum(metrics[k]['failed']) / total_fails
        avg = (sum(metrics[k]['passed']) + sum(metrics[k]['failed'])) \
              / (total_meets + total_fails)
        results[k] = "{:.2f} ({:.2f} passed {:.2f} failed)".format(avg, avg_meets, avg_fails)
    return results

def calc(input_file, data_file, udacity_browser=None, max_num_passed=10, max_num_failed=10):
    """ Calculate scores.

    Args:
        input_file(str): Path to input file.
        data_file(str): Path to the data file (csv).
        udacity_browser(UdacityBrowser): A UdacityBrowser object.
        max_num_passed(int): The number of "meet specifications" reviews to calculate.
        max_num_failed(int): The number of "required changes" reviews to calculate.
    """
    # shortcut to udacity_connection parameter.
    b = udacity_browser

    metrics = {
        'review_use': {'passed': [], 'failed': []},
        'review_clarity': {'passed': [], 'failed': []},
        'review_detail': {'passed': [], 'failed': []},
        'review_personal': {'passed': [], 'failed': []},
        'review_unbiased': {'passed': [], 'failed': []}
    }

    # Loading work in progress file if exists.
    if os.path.exists(data_file):
        data_df = pd.read_csv(data_file)
    else:
        data_df = pd.DataFrame(columns=['submission_id', 'is_passed', 'graded_version'] + list(metrics.keys()))

    data_df.graded_version = data_df.graded_version.astype(str)
    with open(input_file) as f:
        data = json.load(f)

        num_passed = 0
        num_failed = 0
        i = 0
        while num_passed < max_num_passed or num_failed < max_num_failed:
            row = data[i]
            if b is not None and row['submission_id'] not in data_df['submission_id'].values:
                data_row = {k: None for k in metrics.keys()}
                data_row['submission_id'] = row['submission_id']
                is_passed = b.get_is_passed(row['submission_id'], wait=random.uniform(0, 1))
                graded_version = b.get_graded_version(max_graded_version=2, wait=random.uniform(4, 15))
                data_row['graded_version'] = graded_version
                if graded_version <= 2:
                    if is_passed:
                        data_row['is_passed'] = True
                        if num_passed < max_num_passed:
                            print("Status: Meet specifications ({} found)".format(num_passed+1))
                            add_to_metrics(metrics, row['responses']['feedback'], is_passed, data_row=data_row)
                        num_passed += 1
                    else:
                        data_row['is_passed'] = False
                        if num_failed < max_num_failed:
                            print("Status: Requires changes ({} found)".format(num_failed+1))
                            add_to_metrics(metrics, row['responses']['feedback'], is_passed, data_row=data_row)
                        num_failed += 1
                    data_df = data_df.append(data_row, ignore_index=True)
                data_df.to_csv(data_file, index=False)
            else:
                print("Work-in-progress submission ID #{}".format(row['submission_id']))
                data_row = data_df[data_df['submission_id'] == row['submission_id']].iloc[0]
                is_passed = data_row['is_passed']
                graded_version = data_row['graded_version']
                if graded_version.isnumeric() and int(graded_version) <= 2:
                    feedback = []
                    def include_me():
                        for k in metrics:
                            value = data_row[k]
                            feedback.append({'key': k, 'rating': value})
                        add_to_metrics(metrics, feedback, is_passed)
                    if is_passed == 1:
                        if num_passed < max_num_passed:
                            include_me()
                            print("Status: Meet specifications ({} found)".format(num_passed+1))
                        num_passed += 1
                    else:
                        if num_failed < max_num_failed:
                            include_me()
                            print("Status: Requires changes ({} found)".format(num_failed+1))
                        num_failed += 1
            i += 1
    print("Metrics:")
    pprint(metrics)
    results = calc_metrics(metrics)
    print("\n----------------\nResults:")
    pprint(results)
    return results

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.cfg')
    username = config['ACCOUNT']['USERNAME']
    password = config['ACCOUNT']['PASSWORD']
    chromedriver_path = config['APP']['CHROMEDRIVER_PATH']

    b = UdacityBrowser(chromedriver_path=chromedriver_path)
    b.connect()
    b.login(username, password, wait=random.uniform(2, 4))
    feedbacks = b.get_feedbacks(wait=random.uniform(1, 2))
    with open('input.json', 'w') as f:
        f.write(feedbacks)
    calc('input.json', 'data.csv', b)
    b.disconnect()
