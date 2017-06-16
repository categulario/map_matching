-- The A* algorithm
local source_node = ARGV[1]
local dest_node = ARGV[2]
local skip_node = ARGV[3]

redis.call('del', 'astar:visited')

local function shiftdown(heap, startpos, pos)
	local newitem = heap[pos]

	while pos > startpos do
		local parentpos = math.floor(pos/2)
		local parent = heap[parentpos]

		if newitem[1] < parent[1] then
			heap[pos] = parent
			pos = parentpos
		else
			break
		end
	end

	heap[pos] = newitem
end

local function shiftup(heap, pos)
	local endpos = #heap+1
	local startpos = pos
	local newitem = heap[pos]
	local childpos = 2*pos

	while childpos < endpos do
		local rightpos = childpos + 1

		if rightpos < endpos and not (heap[childpos][1] < heap[rightpos][1]) then
			childpos = rightpos
		end

		heap[pos] = heap[childpos]
		pos = childpos
		childpos = 2*pos
	end

	heap[pos] = newitem

	shiftdown(heap, startpos, pos)
end

local function heappush(heap, arg)
	heap[#heap+1] = arg

	shiftdown(heap, 1, #heap)
end

local function pop(list)
	local lastel = list[#list]
	list[#list] = nil
	return lastel
end

local function heappop(heap)
	local lastel = pop(heap)

	if #heap>0 then
		local returnitem = heap[1]
		heap[1] = lastel
		shiftup(heap, 1)
		return returnitem
	end
	
	return lastel
end

local function neighbours(nodeid)
	local result = {}

	for i, way in pairs(redis.call('lrange', 'base:node:'..nodeid..':ways', 0, -1)) do
		local nodes   = redis.call('lrange', 'base:way:'..way..':nodes', 0, -1)
		local highway = redis.call('get', 'base:way:'..way..':highway')
		local oneway  = redis.call('get', 'base:way:'..way..':oneway')
		local normal  = oneway ~= '-1' and oneway ~= 'reverse'
		local oposite = oneway ~= 'yes' and oneway ~= 'true' and oneway ~= '1' and highway ~= 'motorway'

		for j, node in pairs(nodes) do
			if node == nodeid then
				if j+1 <= #nodes and normal and nodes[j+1] ~= skip_node then
					result[#result+1] = {
						redis.call('geodist', 'base:nodehash', node, nodes[j+1], 'm'),
						nodes[j+1]
					}
				end

				if j-1 >= 1 and oposite and nodes[j-1] ~= skip_node then
					result[#result+1] = {
						redis.call('geodist', 'base:nodehash', node, nodes[j-1], 'm'),
						nodes[j-1]
					}
				end
			end
		end
	end

	return result
end

local function concat(t1, t2)
	local res = {}

	for i = 1,#t1 do
		res[i] = t1[i]
	end

	for i = 1,#t2 do
		res[#res+1] = t2[i]
	end

	return res
end

--------
-- A* --
--------

local heap = {
	{0, {source_node}}
}

while #heap > 0 do

	local cost, nodelist = unpack(heappop(heap))
	local lastnode = nodelist[#nodelist]

	if lastnode == dest_node then
		return {cost, redis.call('geopos', 'base:nodehash', unpack(nodelist))}
	end

	if redis.call('sismember', 'astar:visited', lastnode) == 0 then
		redis.call('sadd', 'astar:visited', lastnode)

		for i, neighbour in pairs(neighbours(lastnode)) do
			heappush(heap, {cost + neighbour[1], concat(nodelist, {neighbour[2]})})
		end
	end
end

return 0
