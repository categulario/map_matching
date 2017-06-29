-- Gets all the ways a node belogs to
local ways = {}
local phantoms = {}
local rad = ARGV[1]
-- TODO receive small radius
local lon = ARGV[2]
local lat = ARGV[3]

-----------------------
-- vector operations --
-----------------------
-- add
local function sub(v1, v2)
	return {v1[1]-v2[1], v1[2]-v2[2]}
end

-- subtract
local function add(v1, v2)
	return {v1[1]+v2[1], v1[2]+v2[2]}
end

-- inner product
local function dot(v1, v2)
	return v1[1]*v2[1] + v1[2]*v2[2]
end

-- scalar product
local function prod(a, v)
	return {a*v[1], a*v[2]}
end

-- gets parameter `a` that describes the projection of `p` in line n1->n2
-- in terms of linear combination of n1 and n2
local function get_projection(n1, n2, p)
	local tn2 = sub(n2, n1)
	local tp = sub(p, n1)

	local sol = prod(
		dot(tp, tn2)/dot(tn2, tn2),
		tn2
	)

	return sol[1] / tn2[1]
end

redis.call('del', 'tmp:gps:ways')

-- add to set all ways near a gps position
for i, node in pairs(redis.call('georadius', 'base:nodehash', lon, lat, rad, 'm', 'WITHDIST', 'ASC')) do
	local nodename = node[1]
	local nodedist = node[2]

	for j, way in pairs(redis.call('lrange', 'base:node:'..nodename..':ways', 0, -1)) do
		if redis.call('sadd', 'tmp:gps:ways', way) == 1 then
			-- add the projection of gps in the line
			local wnodes = redis.call('lrange', 'base:way:'..way..':nodes', 0, -1)

			for k = 1 , #wnodes-1 do
				local n1 = redis.call('geopos', 'base:nodehash', wnodes[k])[1]
				local n2 = redis.call('geopos', 'base:nodehash', wnodes[k+1])[1]

				local a = get_projection(n1, n2, {lon, lat})

				-- projection is inside segment
				if a<=1 and a>=0 then
					local phantom_coords = add(prod(a, sub(n2, n1)), n1)
					local phantom_name = wnodes[k]..'-'..wnodes[k+1]
					-- TODO add node to geohash
					-- TODO add node to phantom node set in redis
					-- TODO compare with other phantoms in this segment and choose smallest
					phantoms[#phantoms+1] = { phantom_name, phantom_coords }
				end
			end

			-- TODO replace nodename below with closest phantom
			-- TODO discriminate ways too far from gps, using small radio
			ways[#ways+1] = {
				way,
				nodename
			}
		end
	end
end

return {ways, phantoms}
