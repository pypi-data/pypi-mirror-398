import cz_ossfs
import string


class CZOSSFileSystem(cz_ossfs.OSSFileSystem):
    def __init__(self, endpoint: string, secret: string, token: string, key: string, cz_feature: string = None):
        super(CZOSSFileSystem, self).__init__(endpoint=endpoint, secret=secret, token=token, key=key)
        self.cz_feature = cz_feature

    def exists(self, path, **kwargs):
        if self.cz_feature == 'bulkload':
            bucket_name, obj_name = super().split_path(path)

            connect_timeout = kwargs.get("connect_timeout", None)
            if not obj_name:
                return True

            if super()._call_oss(
                    "object_exists",
                    obj_name,
                    bucket=bucket_name,
                    timeout=connect_timeout,
            ):
                return True

            return False
        else:
            return super().exists(path, **kwargs)
