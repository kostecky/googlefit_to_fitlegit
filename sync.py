#!/usr/bin/env python

import datetime
import logging
import httplib2
import requests
import os
from oauth2client.file import Storage
from apiclient.discovery import build

epoch = datetime.datetime.utcfromtimestamp(0)


def unix_time_nano(dt):
    return (dt - epoch).total_seconds() * 1000000000


class Sources:
    def __init__(self):
        self.google_client = self.get_google_client()

    def get_google_client(self, cred_file='./google.json', ):
        """Returns an authenticated google fit client object"""
        logging.debug("Creating Google client")
        credentials = Storage(cred_file).get()
        http = credentials.authorize(httplib2.Http())
        client = build('fitness', 'v1', http=http)
        logging.debug("Google client created")
        return client

    def get_data(self, data_source_id, dataset_id):
        ret = self.google_client.users().dataSources().datasets().get(
            userId='me',
            dataSourceId=data_source_id,
            datasetId=dataset_id).execute()
        # Insert empty 'point' when there is nothing
        if 'point' not in ret:
            ret['point'] = []
        return ret

    def get_data_source_id(self, data_source):
        return ':'.join((
            data_source['type'],
            data_source['dataType']['name']))

    def get_data_source(self, data_type='weight'):
        # https://www.googleapis.com/fitness/v1/users/me/dataSources/derived:com.google.weight:com.google.android.gms:merge_weight/datasets/${today_start}-${today_end}"
        if data_type == 'weight':
            data_source = dict(
                type='derived',
                application=dict(name='fitsync'),
                dataType=dict(
                    name='com.google.weight:com.google.android.gms:merge_weight',
                    field=[dict(format='floatPoint', name='weight')]
                )
            )
        # https://www.googleapis.com/fitness/v1/users/me/dataSources/raw:com.google.nutrition:com.myfitnesspal.android:/datasets/${yesterday_start}-${today_end}
        elif data_type == 'nutrition':
            data_source = dict(
                type='raw',
                application=dict(name='fitsync'),
                dataType=dict(
                    name='com.google.nutrition:com.myfitnesspal.android:',
                    field=[dict(format='floatPoint', name='nutrition')]
                )
            )
        return data_source


def main():
    now = datetime.datetime.now()
    past = now - datetime.timedelta(days=5)
    tomorrow = now + datetime.timedelta(days=1)

    # Connect to google api
    sources = Sources()

    # Connect to fitlegit
    fl_session = requests.session()
    login_data = dict(username=os.environ['FITLEGIT_USER'], password=os.environ['FITLEGIT_PASS'])
    fl_session.post('http://fitlegitapp.com/login/', login_data)

    # Weight
    # https://www.googleapis.com/fitness/v1/users/me/dataSources/derived:com.google.weight:com.google.android.gms:merge_weight/datasets/${today_start}-${today_end}" | jq '.point[-1].value[0].fpVal
    data_source = sources.get_data_source('weight')
    data_source_id = sources.get_data_source_id(data_source)
    dataset_id = "%d-%d" % (unix_time_nano(past), unix_time_nano(tomorrow))
    dataset = sources.get_data(data_source_id, dataset_id)

    for point in dataset['point']:
        weight_date = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1000000000)
        weight = point['value'][0]['fpVal']
        print "%s: %d" % (weight_date.strftime("%Y-%m-%d"), weight)
        weight_dec = int((round(weight, 1) - int(weight)) * 10)
        weight_data = dict(weight_main="%d" % weight, weight_dec=str(weight_dec), weight_log_date=weight_date.strftime("%Y-%m-%d"))
        print weight_data
        result = fl_session.post('http://fitlegitapp.com/dashboard/log-weight/', weight_data)
        result.raise_for_status()

    # Nutrition
    # https://www.googleapis.com/fitness/v1/users/me/dataSources/raw:com.google.nutrition:com.myfitnesspal.android:/datasets/${yesterday_start}-${today_end}
    # http --form --session=fitlegitapp POST fitlegitapp.com/dashboard/log-calories/ 'calories=1792' 'calorie_log_date=2017-03-17'
    data_source = sources.get_data_source('nutrition')
    data_source_id = sources.get_data_source_id(data_source)
    dataset_id = "%d-%d" % (unix_time_nano(past), unix_time_nano(tomorrow))
    dataset = sources.get_data(data_source_id, dataset_id)

    for point in dataset['point']:
        nutrition_date = datetime.datetime.fromtimestamp(int(point['endTimeNanos']) / 1000000000)
        calories_entry = (item for item in point['value'][0]['mapVal'] if item['key'] == 'calories').next()
        calories = calories_entry['value']['fpVal']
        print "%s: %d" % (nutrition_date.strftime("%Y-%m-%d"), calories)
        calorie_data = dict(calories="%d" % calories, calorie_log_date=nutrition_date.strftime("%Y-%m-%d"))
        print calorie_data
        result = fl_session.post('http://fitlegitapp.com/dashboard/log-calories/', calorie_data)
        result.raise_for_status()

if __name__ == '__main__':
    main()
