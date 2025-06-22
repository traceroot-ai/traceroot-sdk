"""Client for querying logs and traces from AWS"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import boto3

from traceroot.config import TraceRootConfig


class TraceRootClient:
    """Client for querying logs and traces from AWS CloudWatch and X-Ray"""

    def __init__(self,
                 config: Optional[TraceRootConfig] = None,
                 aws_region: Optional[str] = None):
        """
        Initialize the query client.

        Args:
            config: TraceRootConfig instance. If not provided, will use AWS region parameter.
            aws_region: AWS region to use. Only used if config is not provided.
        """
        if config:
            self.aws_region = config.aws_region
            self.log_group = config.cloudwatch_log_group
        else:
            self.aws_region = aws_region or "us-west-2"
            self.log_group = None

        # Initialize AWS clients
        session = boto3.Session(region_name=self.aws_region)
        self.logs_client = session.client('logs')
        self.xray_client = session.client('xray')

    def query_logs_by_trace_id(
            self,
            trace_id: str,
            log_group_name: Optional[str] = None,
            minutes: int = 1440,  # 1 day default
    ) -> List[Dict]:
        """
        Query CloudWatch logs by trace ID.

        Args:
            trace_id: AWS X-Ray format trace ID (1-{8 hex chars}-{24 hex chars})
            log_group_name: CloudWatch log group name. Uses config default if not provided.
            minutes: How many minutes back to search (default: 1440 = 1 day)

        Returns:
            List of log events matching the trace ID

        Example:
            client = TraceRootClient()
            logs = client.query_logs_by_trace_id("1-4bd3ef22-1264608c127ced6a0c99f898")
        """
        if log_group_name is None:
            if self.log_group is None:
                raise ValueError(
                    "log_group_name must be provided or set in config")
            log_group_name = self.log_group

        pattern = f'%trace_id={trace_id}%'
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int(
            (datetime.now() - timedelta(minutes=minutes)).timestamp() * 1000)

        # AWS CloudWatch Logs has a limit on query time range
        # For queries > 1 day, we need to chunk them
        chunk_size = 1440  # 1 day in minutes
        num_chunks = (minutes + chunk_size - 1) // chunk_size

        all_events = []
        for i in range(num_chunks):
            chunk_end = end_time - (i * chunk_size * 60 * 1000)
            chunk_start = max(start_time, chunk_end - (chunk_size * 60 * 1000))

            filter_params = {
                'logGroupName': log_group_name,
                'filterPattern': pattern,
                'startTime': chunk_start,
                'endTime': chunk_end,
            }

            try:
                response = self.logs_client.filter_log_events(**filter_params)
                all_events.extend(response.get('events', []))

                # Handle pagination
                while 'nextToken' in response:
                    filter_params['nextToken'] = response['nextToken']
                    response = self.logs_client.filter_log_events(
                        **filter_params)
                    all_events.extend(response.get('events', []))

            except Exception as e:
                print(f"Error querying chunk {i+1}/{num_chunks}: {e}")
                continue

        # Sort by timestamp
        all_events.sort(key=lambda x: x.get('timestamp', 0))
        return all_events

    def get_trace_by_id(self, trace_id: str) -> Tuple[Dict, List[Dict]]:
        """
        Get X-Ray trace by trace ID.

        Args:
            trace_id: AWS X-Ray format trace ID (1-{8 hex chars}-{24 hex chars})

        Returns:
            Tuple of (trace_data, segments_list)

        Example:
            client = TraceRootClient()
            trace, segments = client.get_trace_by_id("1-4bd3ef22-1264608c127ced6a0c99f898")
        """
        try:
            response = self.xray_client.batch_get_traces(TraceIds=[trace_id])
            if not response.get('Traces'):
                return {}, []

            trace = response['Traces'][0]
            segments = trace.get('Segments', [])
            return trace, segments

        except Exception as e:
            print(f"Error getting trace {trace_id}: {e}")
            return {}, []

    # TODO(xinwei): Remove this if it is not used.
    def query_logs_by_service(
        self,
        service_name: str,
        log_group_name: Optional[str] = None,
        minutes: int = 60,
        level: Optional[str] = None,
    ) -> List[Dict]:
        """
        Query logs by service name.

        Args:
            service_name: Name of the service to query logs for
            log_group_name: CloudWatch log group name. Uses config default if not provided.
            minutes: How many minutes back to search (default: 60)
            level: Log level to filter by (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Returns:
            List of log events for the service
        """
        if log_group_name is None:
            if self.log_group is None:
                raise ValueError(
                    "log_group_name must be provided or set in config")
            log_group_name = self.log_group

        # Build filter pattern
        pattern = f'%service_name={service_name}%'
        if level:
            pattern = f'{pattern} %{level.upper()}%'

        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int(
            (datetime.now() - timedelta(minutes=minutes)).timestamp() * 1000)

        filter_params = {
            'logGroupName': log_group_name,
            'filterPattern': pattern,
            'startTime': start_time,
            'endTime': end_time,
        }

        all_events = []
        try:
            response = self.logs_client.filter_log_events(**filter_params)
            all_events.extend(response.get('events', []))

            # Handle pagination
            while 'nextToken' in response:
                filter_params['nextToken'] = response['nextToken']
                response = self.logs_client.filter_log_events(**filter_params)
                all_events.extend(response.get('events', []))

        except Exception as e:
            print(f"Error querying logs for service {service_name}: {e}")

        # Sort by timestamp
        all_events.sort(key=lambda x: x.get('timestamp', 0))
        return all_events

    # TODO(xinwei): Remove this if it is not used.
    def get_recent_traces(
        self,
        minutes: int = 60,
        service_name: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get recent traces from X-Ray.

        Args:
            minutes: How many minutes back to search (default: 60)
            service_name: Filter by service name if provided

        Returns:
            List of trace summaries
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes)

        filter_expression = None
        if service_name:
            filter_expression = f'service("{service_name}")'

        try:
            response = self.xray_client.get_trace_summaries(
                TimeRangeType='TimeRangeByStartTime',
                StartTime=start_time,
                EndTime=end_time,
                FilterExpression=filter_expression,
            )
            return response.get('TraceSummaries', [])

        except Exception as e:
            print(f"Error getting recent traces: {e}")
            return []
