-- Compute the longest distance between street's nodes
local max_dist = 0
local node1 = nil
local node2 = nil

for i, key in pairs(redis.call('keys', 'mapmatch:way:*:nodes')) do
    local nodes = redis.call('lrange', key, 0, -1)

    for i=1,#nodes-1 do
        local dist = tonumber(redis.call('geodist', 'mapmatch:nodehash', nodes[i], nodes[i+1], 'm'))

        if dist > max_dist then
            max_dist = dist
            node1 = nodes[i]
            node2 = nodes[i+1]
        end
    end
end

local res = {}

res[1] = max_dist
res[2] = node1
res[3] = node2

return res
