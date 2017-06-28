-- Gets all the ways a node belogs to
local ways = {}
local rad = ARGV[1]
local lon = ARGV[2]
local lat = ARGV[3]

redis.call('del', 'tmp:gps:ways')

-- add to set all ways near a gps position
for i, node in pairs(redis.call('georadius', 'base:nodehash', lon, lat, rad, 'm', 'WITHDIST', 'ASC')) do
	local nodename = node[1]
	local nodedist = node[2]

	for j, way in pairs(redis.call('lrange', 'base:node:'..nodename..':ways', 0, -1)) do
		if redis.call('sadd', 'tmp:gps:ways', way) == 1 then
			ways[#ways+1] = {
				way,
				nodename
			}
		end
	end
end

return ways
