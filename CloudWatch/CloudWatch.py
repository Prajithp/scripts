import boto3
import json
import requests
import datetime
import re
import subprocess
import argparse
import sys

class InstanceInfo:
    def __init__(self):
        self.request = requests.Session()
        self.instance_info = self.getInstanceInfo()
        self.__dict__ =  self.instance_info
        
    def getInstanceInfo(self):
        response = self.request.get('http://169.254.169.254/latest/dynamic/instance-identity/document')
        return response.json()

    
class CloudWatch:
    def __init__(self, region, instanceId):
        self.request = requests.Session()
        self.region  = region
        self.instanceId = instanceId
        self.client  = boto3.client('cloudwatch', region_name=region)
        
    def sendMetrics(self, metrics=None, namespace="System/Linux"):
        instance_id = self.instanceId
        if metrics is None:
            metrics = self.metrics()

        for key, metric in metrics.iteritems():
            value = metric
            unit  = 'Percent'
            if type(metric) is dict:
                value = metric['vaule']
                unit  = metric.get('unit', 'Percent')

            self.client.put_metric_data(
                Namespace=namespace, 
                MetricData=[
                    {
                        'MetricName': key,
                        'Dimensions': [{
                            'Name': 'InstanceId',
                            'Value': instance_id
                        }],
                        'Timestamp': datetime.datetime.utcnow(),
                        'Value': float(value),
                        'Unit': unit
                    }
                ]
            )

    def metrics(self):
        raise ImportError("Not Implemented")

class MemMetrics(CloudWatch):
    def __init__(self, region, instanceId):
        CloudWatch.__init__(self, region, instanceId)        
        mem_info = self.gatherMemInfo()
        self.mem_total   = mem_info['MemTotal']
        self.mem_free    = mem_info['MemFree']
        self.mem_cached  = mem_info['Cached']
        self.mem_buffers = mem_info['Buffers']
        self.swap_total  = mem_info['SwapTotal']
        self.swap_free  =  mem_info['SwapFree']

    def gatherMemInfo(self):
        meminfo = {}
        pattern = re.compile('([\w\(\)]+):\s*(\d+)(:?\s*(\w+))?')
        with open('/proc/meminfo') as f:
            for line in f:
                match = pattern.match(line)
                if match:
                    meminfo[match.group(1)] = float(match.group(2))
        return meminfo

    def mem_util(self):
        return 100.0 * self.mem_used() / self.mem_total

    def mem_avail(self):
        return self.mem_free

    def mem_used(self):
        return self.mem_total - self.mem_avail()

    def swap_util(self):
        if self.swap_total == 0:
            return 0

        return 100.0 * self.swap_used() / self.swap_total

    def swap_used(self):
        return self.swap_total - self.swap_free


    def metrics(self):
        mem_usage = self.mem_util()
        swap_usage = self.swap_util()
        return  {
            'MemUsage':  mem_usage,
            'SwapUsage': swap_usage,
        }

class DiskMetrics(CloudWatch):
    def __init__(self, region, instanceId, mount=None):
        CloudWatch.__init__(self, region, instanceId)
        self.mount_point = mount if mount is not None else '/'

    def disk_util(self):
        df = subprocess.Popen(["df", self.mount_point], stdout=subprocess.PIPE)
        output = df.communicate()[0]
        device, size, used, available, percent, mountpoint = output.split("\n")[1].split()
        return percent[0:-1] 
    
    def metrics(self):
        disk_usage = self.disk_util()
        return {
            'DiskSpaceUtilization': disk_usage
        }

class CPUMetrics(CloudWatch):
    def __init__(self, region, instanceId):
        CloudWatch.__init__(self, region, instanceId)

    def gatherLoadAvg(self):
        load_avg_info = {}
        with open('/proc/loadavg', 'r') as loadavg:
            data = loadavg.read().split(' ')
            load_avg_info['1min']  = data[0]
            load_avg_info['5min']  = data[1]
            load_avg_info['15min'] = data[2]

        return load_avg_info
    
    def metrics(self):
        load_avg_info = self.gatherLoadAvg()
        return {
            'LoadAvg1Min':  {'vaule': load_avg_info['1min'], 'unit': 'Count'},
            'LoadAvg5Min':  {'vaule': load_avg_info['5min'], 'unit': 'Count'},
            'LoadAvg15Min': {'vaule': load_avg_info['15min'], 'unit': 'Count'},
        }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''Collect mem, cpu and disk stats from an ec2 instance
         and sends the details to cloudwatch as custom metrics'''
    )

    parser.add_argument('--dump', action='store_true', help='Dump collected data')

    memory = parser.add_argument_group('memory metrics')
    memory.add_argument('--memory', action='store_true', help='collect memory utilization')

    disk = parser.add_argument_group('disk metrics')
    disk.add_argument('--disk', action='store_true', help='collect disk utilization')
    disk.add_argument('--mount-point', default="/", help="specify the mount point to be monitored")

    cpu = parser.add_argument_group('cpu metrics')
    cpu.add_argument('--cpu', action='store_true', help='collect cpu utilization')

    if len(sys.argv) == 1:
        parser.print_help()
        exit()

    args = parser.parse_args()

    instance_info = InstanceInfo()

    if args.memory:
        mem = MemMetrics(instance_info.region, instance_info.instanceId)
        if args.dump:
            print mem.metrics()
        else:
            mem.sendMetrics()
    
    if args.disk:
        path = args.mount_point
        disk = DiskMetrics(instance_info.region, instance_info.instanceId, path)
        if args.dump:
            print disk.metrics()
        else:
            disk.sendMetrics()
    
    if args.cpu:
        cpu = CPUMetrics(instance_info.region, instance_info.instanceId)
        if args.dump:
            print cpu.metrics()
        else:
            cpu.sendMetrics()