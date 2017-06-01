-- Gets all the ways a node belogs to
local ways = {}

-- add to set all ways near a gps position
for i, node in pairs(redis.call('georadius', 'base:nodehash', ARGV[1], ARGV[2], ARGV[3], 'm')) do
	for i, way in pairs(redis.call('lrange', 'base:node:'..node..':ways', 0, -1)) do
		redis.call('sadd', 'track:gps:'..ARGV[4]..':ways', way)
	end
end

-- get position of all nodes of all ways
for i, way in pairs(redis.call('smembers', 'track:gps:'..ARGV[4]..':ways')) do
	ways[i] = {}
	
	for j, node in pairs(redis.call('lrange', 'base:way:'..way..':nodes', 0, -1)) do
		ways[i][j] = {node, redis.call('geopos', 'base:nodehash', node)[1]}
	end
end

return ways
