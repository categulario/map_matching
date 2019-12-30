local ways = {}

-- get position of all nodes of the ways present in the intersection of ways
-- near point 1 and 2
for i, way in pairs(redis.call('sinter', 'track:gps:'..ARGV[1]..':ways', 'track:gps:'..ARGV[2]..':ways')) do
    ways[i] = {}

    for j, node in pairs(redis.call('lrange', 'base:way:'..way..':nodes', 0, -1)) do
        ways[i][j] = {node, redis.call('geopos', 'base:nodehash', node)[1]}
    end
end

return ways
