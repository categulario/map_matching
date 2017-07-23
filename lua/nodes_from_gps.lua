-- Gets all the ways a node belogs to
local nodes     = {}
local small_rad = ARGV[1]
local big_rad   = ARGV[2]
local lon       = ARGV[3]
local lat       = ARGV[4]

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

-- Haversine formula, translated from the python version
local function distance(lon1, lat1, lon2, lat2)
    -- convert decimal degrees to radians
    local r = 0.017453292519943
    local lon1, lat1, lon2, lat2 = lon1*r, lat1*r, lon2*r, lat2*r

    -- haversine formula
    local dlon = lon2 - lon1
    local dlat = lat2 - lat1
    local a = math.pow(math.sin(dlat/2), 2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlon/2), 2)
    local c = 2 * math.asin(math.sqrt(a))
    local m = 6367 * c * 1000

    return m
end

redis.call('del', 'tmp:gps:ways')

-- add to set all ways near a gps position
for i, node in pairs(redis.call('georadius', 'base:nodehash', lon, lat, big_rad, 'm', 'WITHDIST', 'ASC')) do
    local nodename = node[1]
    local nodedist = node[2]

    for j, way in pairs(redis.call('lrange', 'base:node:'..nodename..':ways', 0, -1)) do
        if redis.call('sadd', 'tmp:gps:ways', way) == 1 then
            -- add the projection of gps in the line
            local way_nodes = redis.call('lrange', 'base:way:'..way..':nodes', 0, -1)

            local cphan = nil
            local cdist = 1e309

            for k = 1 , #way_nodes-1 do
                local n1 = redis.call('geopos', 'base:nodehash', way_nodes[k])[1]
                local n2 = redis.call('geopos', 'base:nodehash', way_nodes[k+1])[1]

                local a = get_projection(n1, n2, {lon, lat})

                -- projection is inside segment
                if a<=1 and a>=0 then
                    local lonlat = add(prod(a, sub(n2, n1)), n1)
                    local phantom_name = way_nodes[k]..'_'..way_nodes[k+1]

                    redis.call('geoadd', 'base:nodehash', lonlat[1], lonlat[2], phantom_name)
                    redis.call('sadd', 'tmp:phantoms', phantom_name)
                    redis.call('linsert', 'base:way:'..way..':nodes', 'after', way_nodes[k], phantom_name)
                    redis.call('rpush', 'tmp:phantom:'..phantom_name..':ways', way)
                end
            end
        end
    end
end

return redis.call('georadius', 'base:nodehash', lon, lat, small_rad, 'm', 'WITHDIST', 'ASC')
