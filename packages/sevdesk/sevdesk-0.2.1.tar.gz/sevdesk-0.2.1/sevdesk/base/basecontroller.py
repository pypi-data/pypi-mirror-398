import inspect
from typing import get_type_hints, get_origin, get_args

class BaseController:
    def __init__(self, client):
        self.client = client
    
    @staticmethod
    def parse_response(response, return_type):
        """Wandelt die Response in das entsprechende Model um"""
        if return_type is None:
            return response
        
        # Hole den ursprünglichen Typ (ohne list[] wrapper)
        origin = get_origin(return_type)
        
        # Wenn es eine Liste ist
        if origin is list:
            args = get_args(return_type)
            if args:
                model_class = args[0]
                # Response sollte eine Liste von Dicts sein
                if isinstance(response, dict) and 'objects' in response:
                    # sevDesk API struktur: {"objects": [...]}
                    return [model_class(**item) if isinstance(item, dict) else item 
                            for item in response['objects']]
                elif isinstance(response, list):
                    return [model_class(**item) if isinstance(item, dict) else item 
                            for item in response]
        
        # Einzelnes Model
        elif hasattr(return_type, '__bases__'):  # Check if it's a class
            if isinstance(response, dict):
                # sevDesk API struktur kann auch {"objects": {...}} sein
                if 'objects' in response and isinstance(response['objects'], dict):
                    return return_type(**response['objects'])
                else:
                    return return_type(**response)
        
        return response
    
    @staticmethod
    def request(method, path):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                # Args in kwargs umwandeln
                sig = inspect.signature(func)
                bound_args = sig.bind(self, *args, **kwargs)
                bound_args.apply_defaults()
                
                # Entferne 'self' aus den arguments
                all_kwargs = dict(bound_args.arguments)
                all_kwargs.pop('self', None)
                
                gen = func(self, **all_kwargs)
                
                try:
                    # Pre-request: bis zum yield ausführen
                    next(gen)
                    # veränderte parameter übernehmen
                    for arg in all_kwargs.copy():
                        # gi_frame HACK
                        if gen.gi_frame:
                            all_kwargs[arg] = gen.gi_frame.f_locals[arg]
                    
                    response = self.client.request(method, path, all_kwargs)
                    
                    # Return Type aus der Funktion auslesen
                    try:
                        type_hints = get_type_hints(func)
                        return_type = type_hints.get('return', None)
                    except Exception:
                        return_type = None
                    
                    # Response in Model umwandeln
                    parsed_response = BaseController.parse_response(response, return_type)
                    
                    # Gebe das Ergebnis direkt zurück
                    return parsed_response
                    
                except StopIteration:
                    return None
                    
            wrapper.__name__ = func.__name__
            return wrapper
        return decorator

    @staticmethod
    def get(path):
        return BaseController.request('get', path)

    @staticmethod
    def post(path):
        return BaseController.request('post', path)

    @staticmethod
    def put(path):
        return BaseController.request('put', path)

    @staticmethod
    def delete(path):
        return BaseController.request('delete', path)