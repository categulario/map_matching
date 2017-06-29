-- Deletes all phantom nodes

for i, phantom in pairs(redis.call('smembers', 'tmp:phantoms')) do
	for j, way in pairs(redis.call('lrange', 'tmp:phantom:'..phantom..':ways', 0, -1)) do
		redis.call('lrem', 'base:way:'..way..':nodes', 0, phantom)
	end

	redis.call('del', 'tmp:phantom:'..phantom..':ways')
end

redis.call('del', 'tmp:phantoms')
