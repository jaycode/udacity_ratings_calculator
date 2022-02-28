""" Login, get feedbacks, then find ratings from the last x number of passed and failed projects.
"""
import json
import configparser
from modules.udacity_browser import UdacityBrowser
from pprint import pprint
import pandas as pd
import os
import random

def add_to_metrics(metrics, feedback, is_meet, data_row=None):
    """ Update metrics and optionally data row with given feedback.

    Args:
        metrics(dict): The metrics dict.
        feedback(list): The feedback list from Udacity's student_feedbacks page
        (responses > feedback)
        is_meet(Boolean): True if the project meets specifications.
        data_row(pd.Series): A row from the data.csv file.
    """
    for f in feedback:
        if is_meet:
            metrics[f['key']]['meets'].append(int(f['rating']))
        else:
            metrics[f['key']]['fails'].append(int(f['rating']))
        if data_row is not None:
            data_row[f['key']] = int(f['rating'])

def calc_metrics(metrics, max_rating=5):
    """ Find the average score for each metric.
    """
    results = {}
    for k in metrics:
        total_meets = len(metrics[k]['meets']) * max_rating
        total_fails = len(metrics[k]['fails']) * max_rating
        avg_meets = sum(metrics[k]['meets']) / total_meets
        avg_fails = sum(metrics[k]['fails']) / total_fails
        avg = (sum(metrics[k]['meets']) + sum(metrics[k]['fails'])) \
              / (total_meets + total_fails)
        results[k] = "{:.2f} ({:.2f} meets {:.2f} fails)".format(avg, avg_meets, avg_fails)
    return results

def calc(input_file, data_file, udacity_browser=None, max_num_meets=10, max_num_fails=10):
    """ Calculate scores.

    Args:
        input_file(str): Path to input file.
        data_file(str): Path to the data file (csv).
        udacity_browser(UdacityBrowser): A UdacityBrowser object.
        max_num_meets(int): The number of "meet specifications" reviews to calculate.
        max_num_fails(int): The number of "required changes" reviews to calculate.
    """
    # shortcut to udacity_connection parameter.
    b = udacity_browser

    metrics = {
        'review_use': {'meets': [], 'fails': []},
        'review_clarity': {'meets': [], 'fails': []},
        'review_detail': {'meets': [], 'fails': []},
        'review_personal': {'meets': [], 'fails': []},
        'review_unbiased': {'meets': [], 'fails': []}
    }

    # Loading work in progress file if exists.
    if os.path.exists(data_file):
        data_df = pd.read_csv(data_file)
    else:
        data_df = pd.DataFrame(columns=['submission_id', 'is_included', 'is_meet'] + list(metrics.keys()))

    with open(input_file) as f:
        data = json.load(f)

        num_meets = 0
        num_fails = 0
        i = 0
        while num_meets < max_num_meets or num_fails < max_num_fails:
            row = data[i]
            if b is not None and row['submission_id'] not in data_df['submission_id'].values:
                data_row = {k: None for k in metrics.keys()}
                data_row['submission_id'] = row['submission_id']
                data_row['is_included'] = False
                is_meet = b.is_meet_specifications(row['submission_id'], wait=random.uniform(1, 20))
                if is_meet:
                    data_row['is_meet'] = True
                    if num_meets < max_num_meets:
                        print("Status: Meet specifications ({} found)".format(num_meets+1))
                        add_to_metrics(metrics, row['responses']['feedback'], is_meet, data_row=data_row)
                        data_row['is_included'] = True
                    num_meets += 1
                else:
                    data_row['is_meet'] = False
                    if num_fails < max_num_fails:
                        print("Status: Requires changes ({} found)".format(num_fails+1))
                        add_to_metrics(metrics, row['responses']['feedback'], is_meet, data_row=data_row)
                        data_row['is_included'] = True
                    num_fails += 1
                data_df = data_df.append(data_row, ignore_index=True)
                data_df.to_csv(data_file, index=False)
            else:
                print("Work-in-progress submission ID #{}".format(row['submission_id']))
                data_row = data_df[data_df['submission_id'] == row['submission_id']].iloc[0]
                is_meet = data_row['is_meet']
                is_included = data_row['is_included']
                feedback = []
                if is_included:
                    for k in metrics:
                        value = data_row[k]
                        feedback.append({'key': k, 'rating': value})
                    add_to_metrics(metrics, feedback, is_meet)
                if is_meet == 1:
                    if num_meets < max_num_meets:
                        print("Status: Meet specifications ({} found)".format(num_meets+1))
                    num_meets += 1
                else:
                    if num_fails < max_num_fails:
                        print("Status: Requires changes ({} found)".format(num_fails+1))
                    num_fails += 1
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
