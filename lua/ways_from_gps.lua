-- Gets all the ways a node belogs to
local ways = {}
local lon = ARGV[1]
local lat = ARGV[2]
local dist = ARGV[3]
local layer = ARGV[4]

-- add to set all ways near a gps position
for i, node in pairs(redis.call('georadius', 'base:nodehash', lon, lat, dist, 'm', 'WITHDIST', 'ASC')) do
	local nodename = node[1]
	local nodedist = node[2]

	for j, way in pairs(redis.call('lrange', 'base:node:'..nodename..':ways', 0, -1)) do
		if redis.call('sadd', 'track:gps:'..layer..':ways', way) == 1 then
			ways[#ways+1] = {
				way,
				nodedist
			}

			-- for j, node in pairs(redis.call('lrange', 'base:way:'..way..':nodes', 0, -1)) do
				-- ways[i][2][j] = {node, redis.call('geopos', 'base:nodehash', node)[1]}
			-- end
		end
	end
end

return ways
