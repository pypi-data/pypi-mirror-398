# This is a  "listener" mechanism code. It's responsible for detecting when the wx.ai/wml SDK is imported.

import sys
import importlib.abc
import importlib.util

class WXAIImportLoader(importlib.abc.Loader):
    def __init__(self, original_loader, patch_callback):
        self.original_loader = original_loader
        self.patch_callback = patch_callback

    def create_module(self, spec):
        return self.original_loader.create_module(spec)

    def exec_module(self, module):
        self.original_loader.exec_module(module)
        self.patch_callback()


class WXAIFinder(importlib.abc.MetaPathFinder):
    def __init__(self):
        # call back function run later when detected import
        self.patch_callback = None
        self._triggered = False

    def find_spec(self, fullname, path, target=None):
        if self.patch_callback and not self._triggered and fullname.startswith(('ibm_watsonx_ai', 'ibm_watson_machine_learning')):
            self._triggered = True
            # Temporarily remove the original finder to avoid recursion 
            original_finder = sys.meta_path.pop(0)
            try:
                # Find the spec for the module
                spec = importlib.util.find_spec(fullname)
                if spec and hasattr(spec, 'loader'):
                    # Wrap the original loader with our custom loader
                    spec.loader = WXAIImportLoader(spec.loader, self.patch_callback)
                    return spec
            finally:
                sys.meta_path.insert(0, original_finder)
        return None

WXAI_FINDER_INSTANCE = WXAIFinder()