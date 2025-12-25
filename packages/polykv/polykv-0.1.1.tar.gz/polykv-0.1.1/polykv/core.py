import json
import os
import asyncio

# Check for PyScript/Browser environment
IS_BROWSER = False
try:
    from js import window
    IS_BROWSER = True
except ImportError:
    pass

if not IS_BROWSER:
    from platformdirs import user_config_dir

class PolyKV:
    def __init__(self, app_name: str = "polyKV"):
        self.app_name = app_name
        self.prefix = f"polyKV_{app_name}_"
        self._cache = {}
        
        if not IS_BROWSER:
            self.config_dir = user_config_dir(app_name, roaming=True)
            self.file_path = os.path.join(self.config_dir, f"{app_name}.json")
            self._ensure_dir()
            self._load_sync()
        else:
            # Browser: No initial load needed for cache-first design? 
            # Or load from localStorage? 
            # TS impl reads from localStorage on get. 
            pass

    def _ensure_dir(self):
        if not IS_BROWSER:
            # os.makedirs(..., mode=0o700) might only affect the leaf directory.
            # But default umask usually handles it reasonably. We force 0700 for security.
            os.makedirs(self.config_dir, mode=0o700, exist_ok=True)

    def _load_sync(self):
        if not IS_BROWSER and os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    async def _save(self):
        # Python 'Native' File IO
        if not IS_BROWSER:
             await asyncio.to_thread(self._save_sync)
        # Browser: Saved immediately in set methods, or we can use internal method
        # But localStorage is sync. Python async layer wraps it.

    def _save_sync(self):
        if not IS_BROWSER:
            tmp_path = self.file_path + ".tmp"
            try:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    # Set permissions to 0600 (owner read/write only)
                    os.chmod(tmp_path, 0o600)
                    json.dump(self._cache, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                # Atomic replace
                os.replace(tmp_path, self.file_path)
            except Exception as e:
                # Naive cleanup attempt
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
                raise e

    # --- Internal Browser Helpers ---
    def _web_set(self, key: str, value):
        if IS_BROWSER:
            # Auto-serialize to match other implementations
            serialized = json.dumps(value) 
            window.localStorage.setItem(self.prefix + key, serialized)

    def _web_get(self, key: str):
        if IS_BROWSER:
            val = window.localStorage.getItem(self.prefix + key)
            if val is None: return None
            try:
                return json.loads(val)
            except:
                return None
        return None

    # --- API ---

    async def set_string(self, key: str, value: str):
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            await self._save()

    async def get_string(self, key: str) -> str:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)

    async def set_number(self, key: str, value: float):
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            await self._save()

    async def get_number(self, key: str) -> float:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)

    async def set_bool(self, key: str, value: bool):
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            await self._save()

    async def get_bool(self, key: str) -> bool:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)
    
    async def set_map(self, key: str, value: dict):
        self._validate_map(value)
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            await self._save()

    async def get_map(self, key: str) -> dict:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)

    async def set_list(self, key: str, value: list):
        self._validate_list(value)
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            await self._save()

    async def get_list(self, key: str) -> list:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)

    async def remove(self, key: str):
        if IS_BROWSER:
            window.localStorage.removeItem(self.prefix + key)
        else:
            if key in self._cache:
                del self._cache[key]
                await self._save()

    async def clear(self):
        if IS_BROWSER:
            # Naive clear matching prefix
            keys_to_remove = []
            length = window.localStorage.length
            for i in range(length):
                k = window.localStorage.key(i)
                if k and k.startswith(self.prefix):
                    keys_to_remove.append(k)
            for k in keys_to_remove:
                window.localStorage.removeItem(k)
        else:
            self._cache = {}
            await self._save()

    # --- Validation Helpers ---

    def _validate_value(self, value):
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"PolyKV: Invalid type '{type(value).__name__}'. Only str, int, float, bool are allowed.")
        # Specific check for bool because isinstance(True, int) is True in Python
        # But we allow both so it's fine.

    def _validate_map(self, value: dict):
        if not isinstance(value, dict):
             raise ValueError("PolyKV: Value must be a dict (Map).")
        for k, v in value.items():
            self._validate_value(v)

    def _validate_list(self, value: list):
        if not isinstance(value, list):
             raise ValueError("PolyKV: Value must be a list (List).")
        for v in value:
            self._validate_value(v)

class PolyKVSync:
    """
    Synchronous version of PolyKV for use in scripts without asyncio.
    API is identical to PolyKV but without 'async/await'.
    """
    def __init__(self, app_name: str = "polyKV"):
        self.app_name = app_name
        self.prefix = f"polyKV_{app_name}_"
        self._cache = {}
        
        if not IS_BROWSER:
            self.config_dir = user_config_dir(app_name, roaming=True)
            self.file_path = os.path.join(self.config_dir, f"{app_name}.json")
            self._ensure_dir()
            self._load_sync()
        else:
            pass

    def _ensure_dir(self):
        if not IS_BROWSER:
            os.makedirs(self.config_dir, mode=0o700, exist_ok=True)

    def _load_sync(self):
        if not IS_BROWSER and os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_sync(self):
        # We can duplicate usage of the logic from PolyKV or just copy it here.
        # Copying for independence to avoid messy MRO or mixins for now.
        if not IS_BROWSER:
            tmp_path = self.file_path + ".tmp"
            try:
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    os.chmod(tmp_path, 0o600)
                    json.dump(self._cache, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, self.file_path)
            except Exception as e:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
                raise e

    # --- Internal Browser Helpers ---
    def _web_set(self, key: str, value):
        if IS_BROWSER:
            serialized = json.dumps(value) 
            window.localStorage.setItem(self.prefix + key, serialized)

    def _web_get(self, key: str):
        if IS_BROWSER:
            val = window.localStorage.getItem(self.prefix + key)
            if val is None: return None
            try:
                return json.loads(val)
            except:
                return None
        return None

    # --- API ---

    def set_string(self, key: str, value: str):
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            self._save_sync()

    def get_string(self, key: str) -> str:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)

    def set_number(self, key: str, value: float):
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            self._save_sync()

    def get_number(self, key: str) -> float:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)

    def set_bool(self, key: str, value: bool):
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            self._save_sync()

    def get_bool(self, key: str) -> bool:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)
    
    def set_map(self, key: str, value: dict):
        self._validate_map(value)
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            self._save_sync()

    def get_map(self, key: str) -> dict:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)

    def set_list(self, key: str, value: list):
        self._validate_list(value)
        if IS_BROWSER:
            self._web_set(key, value)
        else:
            self._cache[key] = value
            self._save_sync()

    def get_list(self, key: str) -> list:
        if IS_BROWSER:
            return self._web_get(key)
        return self._cache.get(key)

    def remove(self, key: str):
        if IS_BROWSER:
            window.localStorage.removeItem(self.prefix + key)
        else:
            if key in self._cache:
                del self._cache[key]
                self._save_sync()

    def clear(self):
        if IS_BROWSER:
            keys_to_remove = []
            length = window.localStorage.length
            for i in range(length):
                k = window.localStorage.key(i)
                if k and k.startswith(self.prefix):
                    keys_to_remove.append(k)
            for k in keys_to_remove:
                window.localStorage.removeItem(k)
        else:
            self._cache = {}
            self._save_sync()

    # --- Validation Helpers ---
    def _validate_value(self, value):
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"PolyKV: Invalid type '{type(value).__name__}'. Only str, int, float, bool are allowed.")

    def _validate_map(self, value: dict):
        if not isinstance(value, dict):
             raise ValueError("PolyKV: Value must be a dict (Map).")
        for k, v in value.items():
            value_to_check = v
            self._validate_value(value_to_check)

    def _validate_list(self, value: list):
        if not isinstance(value, list):
             raise ValueError("PolyKV: Value must be a list (List).")
        for v in value:
            self._validate_value(v)
