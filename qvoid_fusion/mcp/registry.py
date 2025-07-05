


model_registry = {}

def register_model(name, model_callable):
    model_registry[name] = model_callable

def get_model(name):
    return model_registry.get(name)

def list_models():
    return list(model_registry.keys())
