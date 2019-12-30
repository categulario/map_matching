local nodes = {}

for i, node in pairs(redis.call('lrange', 'base:way:'..ARGV[1]..':nodes', 0, -1)) do
    nodes[i] = redis.call('geopos', 'base:nodehash', node)[1]
end

return nodes
