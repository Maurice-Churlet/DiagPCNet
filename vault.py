# Copyright (C) 2026 Maurice
# This program is free software under the GNU GPL v3 license.
# See the LICENSE file for details.

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class VaultEngine:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "vault.db")
        self.salt = b'DiagPcNetSalt_2026' # En production, utiliser un sel unique stocké

    def _derive_key(self, password):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def save_vault(self, real_pwd, real_data, fake_pwd, fake_data):
        """Initialise ou met à jour le coffre avec les deux mots de passe."""
        real_key = self._derive_key(real_pwd)
        fake_key = self._derive_key(fake_pwd)
        
        f_real = Fernet(real_key)
        f_fake = Fernet(fake_key)
        
        payload = {
            "real_blob": f_real.encrypt(json.dumps(real_data).encode()).decode(),
            "fake_blob": f_fake.encrypt(json.dumps(fake_data).encode()).decode()
        }
        
        with open(self.config_path, "w") as f:
            json.dump(payload, f)

    def unlock(self, password):
        """Tente d'ouvrir le coffre. Retourne (data, is_real)."""
        if not os.path.exists(self.config_path):
            return None, False
            
        with open(self.config_path, "r") as f:
            payload = json.load(f)
            
        key = self._derive_key(password)
        fernet = Fernet(key)
        
        # On tente d'abord de décrypter le vrai blob
        try:
            data = fernet.decrypt(payload["real_blob"].encode()).decode()
            return json.loads(data), True
        except:
            # Si ça échoue, on tente le blob d'illusion
            try:
                data = fernet.decrypt(payload["fake_blob"].encode()).decode()
                return json.loads(data), False
            except:
                return None, False

    def is_initialized(self):
        return os.path.exists(self.config_path)

    def update_blob(self, password, new_data, is_real):
        """Met à jour uniquement l'un des deux blobs sans avoir besoin de l'autre mot de passe."""
        if not os.path.exists(self.config_path): return False
        
        with open(self.config_path, "r") as f:
            payload = json.load(f)
            
        key = self._derive_key(password)
        fernet = Fernet(key)
        blob = fernet.encrypt(json.dumps(new_data).encode()).decode()
        
        if is_real:
            payload["real_blob"] = blob
        else:
            payload["fake_blob"] = blob
            
        with open(self.config_path, "w") as f:
            json.dump(payload, f)
        return True
