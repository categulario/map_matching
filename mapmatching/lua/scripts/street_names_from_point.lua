local data = {}

for i, node in pairs(redis.call('georadius', 'mapmatch:nodehash', ARGV[1], ARGV[2], 15, 'm')) do
    for j, way in pairs(redis.call('lrange', 'mapmatch:node:'..node..':ways', 0, -1)) do
        data[#data+1] = redis.call('get', 'mapmatch:way:'..way..':name')
    end
end

return data
