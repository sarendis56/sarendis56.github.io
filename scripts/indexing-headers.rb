#!/usr/bin/env ruby
# Print a proxy configuration; never deploy or change the policy flag.
require 'json'
require 'yaml'
require 'uri'
root = File.expand_path('..', __dir__)
policy = JSON.parse(File.read(File.join(root, '_data/indexing.json')))
config = YAML.load_file(File.join(root, '_config.yml'))
host = URI(config.fetch('url')).host
paths = policy.fetch('excluded_paths')
abort 'Invalid paths in exclusion list' unless paths.all? { |p| p.start_with?('/') && !p.match?(/[\r\n]/) }
puts JSON.pretty_generate({
  'description' => 'Noindex excluded academic website documents',
  'expression' => "(http.host eq #{host.to_json} and http.request.uri.path in {#{paths.map(&:to_json).join(' ')}})",
  'action' => 'rewrite',
  'action_parameters' => {'headers' => {'X-Robots-Tag' => {'operation' => 'set', 'value' => 'noindex, nofollow'}}}
})
