class ICollector:
    def __init__(self):
        pass

    def collect_data(self):
        pass
    
class Collector(ICollector):
    def __init__(self):
        super().__init__()