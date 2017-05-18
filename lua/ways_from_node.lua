-- Gets all the ways a node belogs to
local ways = {}

for i, node in pairs(redis.call('georadius', 'mapmatch:nodehash', ARGV[1], ARGV[2], ARGV[3], 'm')) do
	for i, way in pairs(redis.call('lrange', 'mapmatch:node:'..node..':ways', 0, -1)) do
		redis.call('sadd', 'mapmatch:gps:'..ARGV[4]..'ways', way)
	end
end

for i, way in pairs(redis.call('smembers', 'mapmatch:gps:'..ARGV[4]..'ways')) do
	ways[i] = {}
	
	for j, node in pairs(redis.call('lrange', 'mapmatch:way:'..way..':nodes', 0, -1)) do
		ways[i][j] = {node, redis.call('geopos', 'mapmatch:nodehash', node)[1]}
	end
end

return ways
