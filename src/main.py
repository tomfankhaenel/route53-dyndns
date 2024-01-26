import os
import boto3
import requests
import time
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
region_name = os.environ.get('AWS_REGION', 'eu-central-1')
zone_id = os.environ.get('ROUTE53_ZONE')
records = os.environ.get('ROUTE53_RECORDS')
# split env by ","
# todo add try and catch exceptions
records = records.split(',')

def convert_to_record_set_format(name):
    return name.replace('*', '\\052')

def get_current_ip():
    # Use a service like 'httpbin' to get the public IP address
    response = requests.get('https://httpbin.org/ip')
    current_ip = response.json().get('origin', '')
    return current_ip

def get_route53_ip(zone_id, record_name):

    if not (aws_access_key_id and aws_secret_access_key and region_name):
        print("AWS credentials or region not provided in the environment variables.")
        return None
    # Initialize Route 53 client
    route53_client = boto3.client('route53', aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key, region_name=region_name)
    try:
        # Get the hosted zone details
        response = route53_client.list_resource_record_sets(HostedZoneId=zone_id, StartRecordName=record_name)
        # Search for the specific record in the response
        for record_set in response['ResourceRecordSets']:
            # convert the record_name to match backslash escaped format of records
            record_name = convert_to_record_set_format(record_name)
            if record_set['Name'] == record_name and record_set['Type'] == 'A':
                # Assuming A record type, you can modify for other types
                return record_set['ResourceRecords'][0]['Value']

        # If the record is not found
        return None

    except Exception:
        return None

def update_route53_record(zone_id, record_name, new_ip):
    if not (aws_access_key_id and aws_secret_access_key and region_name):
        print("AWS credentials or region not provided in the environment variables.")
        return False

    # Initialize Route 53 client
    route53_client = boto3.client('route53', aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key, region_name=region_name)

    try:
        # Update the Route 53 record with the new IP
        response = route53_client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': record_name,
                            'Type': 'A',
                            'TTL': 300,
                            'ResourceRecords': [
                                {
                                    'Value': new_ip,
                                },
                            ],
                        },
                    },
                ],
            }
        )
        print(f"Route 53 record " + record_name + " updated to " + new_ip)
        return True

    except Exception as e:
        print(f"Error updating Route 53 record: {e}")
        return False

while True:
    current_ip = get_current_ip()
    for record_name in records:
        route53_ip = get_route53_ip(zone_id, record_name)

        if current_ip != route53_ip:
            print("current: " + current_ip + " old: " + route53_ip + " for record: " + record_name + " updating to current ip ...")
            update_route53_record(zone_id, record_name, current_ip)
        else:
            print("current: " + current_ip + " old: " + route53_ip + " for record: " + record_name + " nothing to do ...")
    print("sleeping a while")
    time.sleep(300)  # Sleep for 5 minutes before checking again