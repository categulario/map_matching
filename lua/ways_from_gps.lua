-- Gets all the ways a node belogs to
local ways = {}
local rad = ARGV[1]
local lon = ARGV[2]
local lat = ARGV[3]

-- vector subtraction
local function vsub(v1, v2)
	return {v1[1]-v2[1], v1[2]-v2[2]}
end

-- vector inner product
local function dot(v1, v2)
	local ret = 0

	for i = 1, #v1 do
		ret = ret + a[i] * b[i]
	end

	return ret
end

-- vector scalar product
local function prod(a, v)
	res = {}

	for i = 1, #v do
		res[#res+1] = v[i]*a
	end

	return res
end

-- gets parameter `a` that describes the projection of `p` in line n1->n2
-- in terms of linear combination of n1 and n2
local function get_projection(n1, n2, p)
	local tn2 = vsub(n2, n1)
	local tp = vsub(p, n1)

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
			ways[#ways+1] = {
				way,
				nodename
			}
		end
	end
end

return ways
