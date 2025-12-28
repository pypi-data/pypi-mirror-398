from decimal import Decimal

from convocations.aws.base import yielder
from convocations.base.utils import dump_yaml


def yield_logs(group, stream, start_time=None, session=None, client=None):
    """
    yields log lines from the specified group and stream from the specified
    start time onwards
    """
    client = client or session.client('logs')
    kwargs = {
        'logGroupName': group,
        'logStreamName': stream,
        'startFromHead': True,
    }
    if start_time:
        kwargs['startTime'] = start_time + 1
    next_token = 'sesame'
    while next_token:
        last_token = next_token
        response = client.get_log_events(**kwargs)
        if not response['events']:
            break
        yield from response['events']
        next_token = response.get('nextForwardToken')
        if next_token == last_token:
            break
        kwargs['nextToken'] = next_token


def get_bucket_size(session, buckets):
    from datetime import datetime, timedelta
    from pytz import utc
    cw = session.client('cloudwatch')
    end_time = datetime.now(tz=utc)
    start_time = end_time - timedelta(days=2)
    metric_name = 'BucketSizeBytes'
    response = yielder(
        cw, 'list_metrics', session=session,
        Namespace='AWS/S3', MetricName=metric_name)
    relevant_metrics = []
    for metric in response:
        bucket = None
        storage_type = None
        for dimension in metric['Dimensions']:
            if dimension['Name'] == 'BucketName':
                bucket = dimension['Value']
            elif dimension['Name'] == 'StorageType':
                storage_type = dimension['Value'].lower()
        if bucket in buckets:
            relevant_metrics.append([bucket, storage_type, metric])
    response = cw.get_metric_data(
        MetricDataQueries=[{
            'Id': f'bucket_{i}_{storage_type}',
            'MetricStat': {
                'Metric': metric,
                'Period': 24 * 60 * 60,
                'Stat': 'Maximum',
                'Unit': 'Bytes',
            },
            'Label': f'{bucket}',
            'ReturnData': True,
        } for i, (bucket, storage_type, metric) in enumerate(relevant_metrics, 1)],
        StartTime=start_time,
        EndTime=end_time,
    )
    rows = []
    for x in response['MetricDataResults']:
        bucket = x['Label']
        storage_type = x['Id'].split('_')[-1]
        timestamps = x['Timestamps']
        if timestamps:
            t = timestamps[0]
            size = Decimal(x['Values'][0])
            size = size / Decimal(1024) / Decimal(1024) / Decimal(1024)
            size.quantize(Decimal('0.1'))
            rows.append([ bucket, t, size, storage_type ])
    return rows
