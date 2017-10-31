#!/usr/bin/env ruby

require 'aws-sdk'
require 'json'
require "net/http"

class CloudWatch
    attr_accessor :instance_info, :client
    attr_reader :region, :instance_id
    def initialize
        response = Net::HTTP.get_response('http://169.254.169.254/latest/dynamic/instance-identity/document')
        self.instance_info = JSON.parse(response)
        self.region = self.instance_info.fetch('region')
        self.instance_id =  self.instance_info.fetch('instance_id')
        self.client == AWS::CloudWatch::Client.new(region: self.region)
    end

    def sendMatrics(metrics: nil, namespace: "System/Linux")
        $instance_id = self.instance_id
        if metics.nil?
            metrics = self.metrics
        end

        metrics.each do |name, metric|
            value = metrics
            unit = 'Percent'
            if metrics.is_a?(HASH)
                value = metrics.fetch('value')
                unit  = metrics.fetch('unit', 'Percent')
            end
            self.client.put_metric_data(
                namespace: namespace, 
                metric_data: [
                    {
                        metric_name: key,
                        diamensions: [{
                            name: 'InstanceId',
                            value: instance_id
                        }],
                        timestamp: Time.now.utc,
                        value: value.to_f,
                        unit: unit
                    }
                ]
            )
        end
    end

    def metric
        raise NoMethodError, "Method not implemented"
    end
end

class MemMetrics
    attr_reader :mem_total, :mem_free, :mem_cached
    attr_reader :mem_buffers, :swap_total, :swap_free
    def initialize
        mem_info = self.gatherMemInfo()
        @mem_total   = mem_info['MemTotal']
        @mem_free    = mem_info['MemFree']
        @mem_cached  = mem_info['Cached']
        @mem_buffers = mem_info['Buffers']
        @swap_total  = mem_info['SwapTotal']
        @swap_free   = mem_info['SwapFree']
    end

    def gatherMemInfo()
        mem_info = {}
        pattern  = /^(?<key>\S*):\s*(?<value>\d*)\s*kB/
        
        mem_file = File.read('/proc/meminfo')
        mem_file.each_line do |line|
            if match = pattern.match(line)
                mem_info[match[:key]] = match[:value].to_i
            end
        end
        return mem_info
    end

    def mem_avail
        return self.mem_free
    end

end

if __FILE__ == $0
    mem = MemMetrics.new
    p mem.mem_avail
end