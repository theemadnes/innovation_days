#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Alex Mattson
# Lambda function sample code that will look for EC2 instances matching a tag 'BackMeUp'
# then create snapshot of the root volume 'xvda' and maintain a rolling set of N (user-defined) snaps at any given time
# NOTE - running this too frequenly will result in API throttling

import boto3
import datetime
import os

client = boto3.client('ec2') # create client to ec2

def lambda_handler(event, context):

    reservations = client.describe_instances(Filters=[{'Name': 'tag-key',
            'Values': ['BackMeUp']}]).get('Reservations', [])
    instances = sum([[i for i in r['Instances']] for r in
                    reservations], [])

    volumes_to_snap = []

    # first get the volumes we want to snapshot (ie root volumes of linux hosts)
    for instance in instances:
        for device in instance['BlockDeviceMappings']:
            # make sure the instance has EBS volumes
            if device.get('Ebs', None) is None:
                continue

            # check to see if device is Linux boot volume, because that's all we're snapping here
            if device['DeviceName'] == '/dev/xvda':
                volumes_to_snap.append(device['Ebs']['VolumeId'])

    # now find the snapshots associated with the volume and create a new one and make sure only the 3 newest are retained
    for volume in volumes_to_snap:
        snap_response = client.create_snapshot(VolumeId=volume)
        print("created snapshot " + snap_response['SnapshotId'] + " for volume " + volume)

        get_snap_response = client.describe_snapshots(Filters=[
            {
                'Name': 'volume-id',
                'Values': [
                    volume,
                ]
            },
        ])

        if len(get_snap_response['Snapshots']) > int(os.environ['snaps_to_retain']):
            print("total snapshot count of " + str(len(get_snap_response['Snapshots']))
                + " for volume " + volume + " exceeds maximum retention of "
                + os.environ['snaps_to_retain'] +  " snaps per volume. cleaning up older snaps...")
            # build list of tuples of 'SnapshotId' & 'StartTime'
            snap_list = []

            for snap in get_snap_response['Snapshots']:
                snap_list.append((snap['SnapshotId'], snap['StartTime']))

            snap_list.sort(key=lambda tup: tup[1], reverse=True)
            # trim list to remove the N newest snaps from deletion process
            snap_list = snap_list[int(os.environ['snaps_to_retain']):]

            for snap in snap_list:
                delete_snap_response = client.delete_snapshot(
                    SnapshotId=snap[0],
                    DryRun=False
                )
                print("deleted snapshot " + snap[0] + " for volume " + volume)

if __name__ == '__main__':
    lambda_handler(None, None)
