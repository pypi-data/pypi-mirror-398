from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Dict

from google.protobuf.message import Message

from clickzetta.connector.v0.exceptions import CZException
from clickzetta_ingestion._proto import ingestion_pb2, ingestion_v2_pb2

T = TypeVar('T', bound=Message)


class RpcMessage(Generic[T], ABC):
    @abstractmethod
    def method(self) -> ingestion_pb2.MethodEnum:
        pass

    @abstractmethod
    def get(self) -> T:
        pass


class AbstractRequest(RpcMessage[T], ABC):
    def __init__(self, method: ingestion_pb2.MethodEnum, message: T):
        self._method = method
        self._message = message

    def method(self) -> ingestion_pb2.MethodEnum:
        return self._method

    def get(self) -> T:
        return self._message

    @abstractmethod
    def account(self, user_name: str, user_id: int = None):
        pass

    def _reset(self, message: T):
        self._message = message


class RpcRequest(AbstractRequest[T]):
    @staticmethod
    def build_account(instance_id: int, workspace: str, user_name: str = "",
                      user_id: int = 0, token: str = "") -> ingestion_v2_pb2.Account:
        """Build account info for requests"""
        account = ingestion_v2_pb2.Account()

        # Set user identifier
        user_ident = ingestion_v2_pb2.UserIdentifier()
        user_ident.instance_id = instance_id
        user_ident.workspace = workspace
        user_ident.user_name = user_name
        user_ident.user_id = user_id

        account.user_ident.CopyFrom(user_ident)
        account.token = token

        return account

    def account(self, user_name: str, user_id: int = None):
        """Add account info to request"""
        # Build account
        account = ingestion_v2_pb2.Account()
        user_ident = ingestion_v2_pb2.UserIdentifier()
        user_ident.user_name = user_name
        if user_id is not None:
            user_ident.user_id = user_id
        account.user_ident.CopyFrom(user_ident)

        # Handle different request types
        message = self.get()
        if isinstance(message, (
                ingestion_v2_pb2.CommitRequest,
                ingestion_v2_pb2.CreateOrGetStreamRequest,
                ingestion_v2_pb2.CloseStreamRequest,
                ingestion_v2_pb2.CheckCommitResultRequest,
        )):
            message.account.CopyFrom(account)
        else:
            raise NotImplementedError(
                f"Unsupported request type for account: {self.method()} {type(message)}"
            )


class ServerTokenMap:
    """Map for managing server tokens"""
    UNKNOWN_TABLET_ID = -1

    def __init__(self, schema_name: str, table_name: str):
        self.schema_name = schema_name
        self.table_name = table_name
        self.server_tokens: Dict[int, str] = {}

    def update(self, new_token):
        """Update server tokens
        
        Args:
            new_token: Either a ScalarMapContainer of {tablet_id: token} or a single token string
        """
        if isinstance(new_token, str):
            # Handle legacy single token update
            if len(self.server_tokens) > 1:
                raise CZException(
                    f"Table {self.schema_name}.{self.table_name} has multiple tablets, "
                    "please call update(Dict[int, str]) instead"
                )

            # Normalize null to empty string
            new_token = "" if not new_token else new_token

            if not self.server_tokens:
                self.server_tokens[self.UNKNOWN_TABLET_ID] = new_token
                return

            old_token = next(iter(self.server_tokens.values()))
            if old_token is None or old_token == "":
                # Keep the old key since it might be the actual tabletId
                old_key = next(iter(self.server_tokens.keys()))
                self.server_tokens[old_key] = new_token
            elif old_token != new_token:
                raise CZException(
                    f"Table {self.schema_name}.{self.table_name} serverToken is not same, "
                    f"old: {old_token}, new: {new_token}"
                )
        elif hasattr(new_token, "items"):
            # Update token map
            for tablet_id, new_token in new_token.items():
                old_token = self.server_tokens.get(tablet_id)
                if old_token is None or old_token == "":
                    self.server_tokens[tablet_id] = new_token
                elif old_token != new_token:
                    raise CZException(
                        f"Table {self.schema_name}.{self.table_name} tabletId {tablet_id}, "
                        f"serverToken is not same, old: {old_token}, new: {new_token}"
                    )
        else:
            raise CZException(f"Invalid server token type: {type(new_token)}")

    def get_server_tokens(self) -> Dict[int, str]:
        """Get all server tokens"""
        return self.server_tokens

    def get_legacy_server_token(self) -> str:
        """Get legacy server token for backward compatibility"""
        if len(self.server_tokens) > 1:
            raise CZException(
                f"Table {self.schema_name}.{self.table_name} has multiple tablets, "
                "please call get_server_tokens() instead"
            )
        return "" if not self.server_tokens else next(iter(self.server_tokens.values()))

    def is_legacy_server_token_required(self) -> bool:
        """Check if legacy server token is required"""
        return not self.server_tokens or self.UNKNOWN_TABLET_ID in self.server_tokens

    def reset(self):
        """Reset all server tokens"""
        self.server_tokens.clear()

    def __str__(self) -> str:
        return (f"ServerTokenMap(schema_name={self.schema_name}, "
                f"table_name={self.table_name}, "
                f"server_tokens={self.server_tokens})")
