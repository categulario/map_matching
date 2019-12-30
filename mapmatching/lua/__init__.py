import os


class LuaManager:

    def __init__(self, redis):
        self.redis = redis
        self.scripts = {}

    def __getattr__(self, name):
        if name in self.scripts:
            return self.scripts[name]

        script_path = os.path.join(
            os.path.dirname(__file__), 'scripts/{name}.lua'.format(name=name)
        )

        if not os.path.isfile(script_path):
            raise ValueError('Script does not exist: {}'.format(name))

        with open(script_path) as script_file:
            self.scripts[name] = self.redis.register_script(script_file.read())

        return self.scripts[name]
