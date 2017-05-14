local count=0

for index, key in pairs(redis.call('keys', ARGV[1])) do
	redis.call('del', key)
	count = count + 1
end

return count
