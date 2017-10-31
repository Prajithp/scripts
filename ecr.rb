#!/usr/bin/env ruby

require 'aws-sdk'
require 'optparse'

module ECR
    class Repository
        attr_reader :name, :registory_id, :ecr

        class << self
            def create(credentials, region_name: 'ap-southeast-1', name: nil)
                return if name.nil?
                ecr = Aws::ECR::Client.new(
                    region: region_name,
                    credentials: credentials,
                )    

                response = ecr.create_repository({ repository_name: name })
                registry_id = response.repository.registry_id
                new(ecr , name, registry_id)
            end
        end
    
        def initialize(ecr, name, registory_id)
            @name = name
            @ecr  = ecr
            @registory_id = registory_id
        end

        def allow_access(user_arn)
            arn = Array.new
            user_arn.is_a?(Array) ? arn.push(*user_arn) : arn.push(user_arn)

            @ecr.set_repository_policy({
                registry_id: @registry_id,
                repository_name: @name,
                policy_text: policy(arn),
                force: false,
            })
        end
      
        def policy(user_arn)
            {
                Version: '2008-10-17',
                Statement: [{
                    Sid: 'jenkins and xxxxx-ecs',
                    Effect: 'Allow',
                    Principal: { AWS: user_arn },
                    Action: [
                        'ecr:GetDownloadUrlForLayer',
                        'ecr:BatchGetImage',
                        'ecr:BatchCheckLayerAvailability',
                        'ecr:PutImage',
                        'ecr:InitiateLayerUpload',
                        'ecr:UploadLayerPart',
                        'ecr:CompleteLayerUpload',
                        'ecr:ListImages',
                        'ecr:ecr:DescribeImages'
                    ]
                }]
            }.to_json
        end
    end
end

if __FILE__ == $0
    options = {}
    optparse = OptionParser.new do |opts|
        opts.banner = "Usage #{$0} [options]"
        opts.on('-u', '--user USERNAME', 'AWS api username') do |user|
            options[:username] = user
        end
        opts.on('-s', '--secret SECRET', 'AWS api secret') do |secret|
            options[:secret] = secret
        end
        opts.on('-r', '--repository REPONAME', 'Repository name') do |repo|
            options[:repository] = repo
        end
        opts.on('-a', '--arn User arn id', 'use "," for adding mutiple id') do |arn|
            user_arn = arn.include?(',') ? arn.split(',') : [arn]
            options[:arn] = user_arn.select{ |_arn| _arn.strip }
        end
        opts.on('-h', '--help', 'Display this screen') do
            puts opts
            exit
        end
    end

    begin
        optparse.parse!
        mandatory = [:username, :secret, :repository]
        missing = mandatory.select{ |param| options[param].nil? }
        unless missing.empty?
          raise OptionParser::MissingArgument.new(missing.join(', '))
        end
    rescue OptionParser::InvalidOption, OptionParser::MissingArgument => e
        puts e.to_s
        puts optparse
        exit                                                                 
    end
end

credentials = Aws::Credentials.new(options[:username], options[:secret])
@ecr = nil
begin
    @ecr = ECR::Repository.create(credentials, name: options[:repository])
    @ecr.allow_access(options[:arn])
rescue Aws::ECR::Errors::RepositoryAlreadyExistsException => e
rescue Exception => e
    abort(e.inspect)
end
    
