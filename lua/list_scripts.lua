local scripts = {}

for i, key in pairs(redis.call('keys', 'mapmatch:script:*')) do
	scripts[i] = {key, redis.call('get', key)}
end

return scripts
