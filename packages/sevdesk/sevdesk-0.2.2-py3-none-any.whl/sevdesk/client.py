import requests
import re
import importlib
from pathlib import Path

class Dummy:
    pass

# Importiere Helper
from sevdesk.helpers import (
    ContactHelper, InvoiceHelper, LetterHelper, BankHelper,
    VoucherHelper, OrderHelper, CreditNoteHelper, PartHelper
)

class Client:

    def __init__(self, api_token, api_base='https://my.sevdesk.de/api/v1', session=None):
        self.api_token = api_token
        self.api_base = api_base
        self.session = session
        if not self.session:
            self.session = requests.Session()

        # Automatisch alle Controller laden
        controllers_dir = Path(__file__).parent / "controllers"
        self._load_controllers(controllers_dir, self, "sevdesk.controllers")
        
        self.undocumented = Dummy()
        controllers_dir2 = Path(__file__).parent / "undocumented" / "controllers"
        self._load_controllers(controllers_dir2, self.undocumented, "sevdesk.undocumented.controllers")
        
        # Helper laden
        self.contactHelper = ContactHelper(self)
        self.invoiceHelper = InvoiceHelper(self)
        self.letterHelper = LetterHelper(self)
        self.bankHelper = BankHelper(self)
        self.voucherHelper = VoucherHelper(self)
        self.orderHelper = OrderHelper(self)
        self.creditNoteHelper = CreditNoteHelper(self)
        self.partHelper = PartHelper(self)


    def _load_controllers(self, controllers_dir, target, module_path):
        """Lädt automatisch alle Controller aus dem controllers Verzeichnis"""
        # controllers_dir = Path(__file__).parent / "controllers"
        
        if not controllers_dir.exists():
            return
        
        for controller_file in controllers_dir.glob("*_controller.py"):
            # z.B. "contact_controller.py" -> "contact"
            controller_name = controller_file.stem.replace("_controller", "")
            
            try:
                # Dynamisch importieren
                module = importlib.import_module(f"{module_path}.{controller_file.stem}")
                
                # Finde die Controller-Klasse im Modul (endet mit "Controller")
                # Wichtig: Nur Klassen die IN DIESEM Modul definiert sind, nicht importierte
                controller_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        attr_name.endswith("Controller") and
                        attr_name != "BaseController" and
                        attr.__module__ == module.__name__):  # Nur aus diesem Modul!
                        controller_class = attr
                        break
                
                if controller_class:
                    # Als Attribut setzen: self.contact = ContactController(self)
                    setattr(target, controller_name, controller_class(self))
                else:
                    print(f"Warning: No controller class found in {controller_file.stem}")
                
            except (ImportError, AttributeError) as e:
                print(f"Warning: Could not load controller {controller_name}: {e}")

    def request(self, method, path, params):
        url_params = re.findall(r"{(\w+)}", path)
        request_path = path.format(**params)
        
        request_params = {
            k: v for k, v in params.items()
            if k not in url_params and
            k != 'body' and
            v} # v not None
        request_url = f'{self.api_base}{request_path}'
        request_body = params.get('body', None)
        if request_body:
            request_body = request_body.model_dump(by_alias=True, exclude_none=True)

        # print('request_params', request_params)
        # print('request_url', request_url)
        # print('request_body', request_body)

        response = self.session.request(
            method=method,
            url=request_url,
            params=request_params,
            json=request_body,
            headers={
                'Authorization': self.api_token
            }
        )
        # print(response.status_code)
        # print(response.text)
        content_type = response.headers.get('content-type', '').lower()
        
        # PDF oder andere Binary-Daten
        if 'application/pdf' in content_type:
            return response.content
        
        # Andere Binary-Formate
        elif any(binary_type in content_type for binary_type in [
            'application/octet-stream',
            'image/',
            'application/zip',
            'application/xml'  # Für invoiceGetXml
        ]):
            return response.content
        else:
            return response.json()