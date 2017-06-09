-- The A* algorithm
local source_node = ARGV[1]
local dest_node = ARGV[2]

local function shiftdown(heap, startpos, pos)
	local newitem = heap[pos]

	while pos > startpos do
		local parentpos = math.floor(pos/2)
		local parent = heap[parentpos]

		if newitem < parent then
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

		if rightpos < endpos and not (heap[childpos] < heap[rightpos]) then
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
