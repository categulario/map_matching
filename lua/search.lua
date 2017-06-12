local str = ARGV[1]
local pattern = ARGV[2]
local keys = {}

for i, key in pairs(redis.call('keys', pattern)) do
	local pos = string.find(redis.call('get', key), str)

	if pos ~= nil then
		keys[#keys+1] = key
	end
end

return keys
