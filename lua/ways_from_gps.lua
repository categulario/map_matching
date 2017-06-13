-- Gets all the ways a node belogs to
local ways = {}
local lon = ARGV[3]
local lat = ARGV[4]
local dist = ARGV[1]
local layer = ARGV[2]

redis.call('del', 'track:gps:'..layer..':ways')

-- add to set all ways near a gps position
for i, node in pairs(redis.call('georadius', 'base:nodehash', lon, lat, dist, 'm', 'WITHDIST', 'ASC')) do
	local nodename = node[1]
	local nodedist = node[2]

	for j, way in pairs(redis.call('lrange', 'base:node:'..nodename..':ways', 0, -1)) do
		if redis.call('sadd', 'track:gps:'..layer..':ways', way) == 1 then
			ways[#ways+1] = {
				way,
				nodedist,
				nodename
			}
		end
	end
end

return ways
