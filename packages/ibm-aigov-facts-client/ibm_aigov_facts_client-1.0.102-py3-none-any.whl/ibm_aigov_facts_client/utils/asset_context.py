class AssetContext:
    """A shared context for asset_id."""
    _asset_id = None
    _catalog_id = None

    @classmethod
    def set_asset_id(cls, asset_id: str):
        """Set the asset_id in the shared context."""
        cls._asset_id = asset_id

    @classmethod
    def get_asset_id(cls):
        """Get the asset_id from the shared context."""
        # if cls._asset_id is None:
        #     raise ValueError("Asset ID is not available. Make sure export_payload was called first.")
        return cls._asset_id
    
    @classmethod
    def set_catalog_id(cls, catalog_id: str):
        """Set the asset_id in the shared context."""
        cls._catalog_id = catalog_id

    @classmethod
    def get_catalog_id(cls):
        """Get the asset_id from the shared context."""
        return cls._catalog_id