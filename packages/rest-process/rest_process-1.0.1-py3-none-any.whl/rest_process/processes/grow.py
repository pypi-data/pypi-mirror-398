from process_bigraph import Process

class GrowProcess(Process):
    config_schema = {
        'rate': 'float'}

    def inputs(self):
        return {'mass': 'float'}

    def outputs(self):
        return {'mass_delta': 'float'}

    def update(self, state, interval):
        return {
            'mass_delta': state['mass'] * self.config['rate'] * interval}
