local data = {}

for number, nodeid in pairs(redis.call('georadius', 'mapmatch:nodehash', ARGV[1], ARGV[2], 15, 'm')) do
	data[nodeid] = redis.call('lrange', 'mapmatch:')
end

return data
