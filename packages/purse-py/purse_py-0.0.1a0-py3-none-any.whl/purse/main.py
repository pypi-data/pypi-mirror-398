from typing import TYPE_CHECKING, Any

from ape.contracts import (
    ContractInstance,
    ContractCallHandler,
    ContractTransactionHandler,
    ContractEvent,
)
from ape.utils import ManagerAccessMixin, cached_property, ZERO_ADDRESS
from ape.types import AddressType, ContractLog, HexBytes

if TYPE_CHECKING:
    from ape.api import AccountAPI
    from ape.api.address import BaseAddress
    from ape.api.transactions import ReceiptAPI

    from .accessory import Accessory


class Purse(ManagerAccessMixin):
    def __init__(
        self,
        account: "AccountAPI | BaseAddress | AddressType",
        *accessories: "Accessory",
    ):
        from ape.api import AccountAPI

        self.address = self.conversion_manager.convert(account, AddressType)

        if isinstance(account, AccountAPI):
            self.wallet = account

        self.accessories = set(accessories)

        # Installed accessories in wallet, indexed by method ID
        self._cached_accessories_by_method_id = {
            method: accy for accy in accessories for method in accy.methods
        }

    @classmethod
    def initialize(
        cls,
        account: "AccountAPI",
        *accessories: "Accessory",
        singleton: "AddressType | None" = None,
    ):
        assert singleton, "Needs support for package version"
        account.set_delegate(
            singleton,
            data=singleton.update_accessories.encode_input(
                [method.model_dump() for accy in accessories for method in accy.methods]
            ),
        )

        return cls(account, *accessories)

    @cached_property
    def wallet(self) -> "AccountAPI | None":
        if self.address in self.accounts_manager:
            return self.accounts_manager[self.address]

        return None

    @cached_property
    def contract(self) -> ContractInstance:
        # NOTE: Use `Purse` as proxy type
        return self.local_project.Purse.at(self.address)

    def _update_cache_from_logs(self, *logs: "ContractLog"):
        from purse.accessory import Accessory, AccessoryMethod

        for log in logs:
            if (
                log.contract_address == self.address
                and log.event_name == "AccessoryUpdated"
            ):
                old = AccessoryMethod(method=log.method, accessory=log.old_accessory)
                new = AccessoryMethod(method=log.method, accessory=log.new_accessory)

                if new.accessory != ZERO_ADDRESS:
                    try:
                        accessory = next(
                            accy
                            for accy in self.accessories
                            if accy.address == new.accessory
                        )

                    except StopIteration:
                        self.accessories.add(accessory := Accessory(new.accessory))

                    self._cached_accessories_by_method_id[new.method] = accessory

                elif old.accessory != ZERO_ADDRESS:
                    if old.method in self._cached_accessories_by_method_id:
                        del self._cached_accessories_by_method_id[old.method]

                    try:
                        accessory = next(
                            accy
                            for accy in self.accessories
                            if accy.address == old.accessory
                        )

                    except StopIteration:
                        continue

                    if all(
                        method.method not in self._cached_accessories_by_method_id
                        for method in accessory.methods
                    ):
                        self.accessories.remove(accessory)

    def add_accessories(
        self,
        *accessories: "Accessory",
        **txn_args,
    ) -> "ReceiptAPI":
        if not accessories:
            raise RuntimeError("Must provide at least one accessory")

        updates: list[dict] = [
            method.model_dump() for accy in accessories for method in accy.methods
        ]

        if "sender" not in txn_args and self.wallet:
            txn_args["sender"] = self.wallet

        receipt = self.contract.update_accessories(updates, **txn_args)

        self._update_cache_from_logs(*receipt.events)

        return receipt

    def remove_methods(
        self,
        *methods: "str | HexBytes",
        **txn_args,
    ) -> "ReceiptAPI":
        from purse.accessory import AccessoryMethod

        if not methods:
            raise RuntimeError("Must provide at least one accessory method")

        updates: list[dict] = [
            AccessoryMethod(accessory=ZERO_ADDRESS, method=method).model_dump()
            for method in methods
        ]

        if "sender" not in txn_args and self.wallet:
            txn_args["sender"] = self.wallet

        receipt = self.contract.update_accessories(updates, **txn_args)

        self._update_cache_from_logs(*receipt.events)

        return receipt

    def remove_accessories(
        self,
        *accessories: "Accessory",
        **txn_args,
    ) -> "ReceiptAPI":
        return self.remove_methods(
            *(m.method for accy in accessories for m in accy.methods),
            **txn_args,
        )

    def __getattr__(self, name: str) -> Any:
        if attr := getattr(self.contract, name, None):
            return attr

        for accy in self.accessories:
            if attr := getattr(accy.contract, name, None):
                match attr:
                    case ContractCallHandler():
                        return ContractCallHandler(
                            contract=self.contract, abis=attr.abis
                        )

                    case ContractTransactionHandler():
                        return ContractTransactionHandler(
                            contract=self.contract, abis=attr.abis
                        )

                    case ContractEvent():
                        return ContractEvent(contract=self.contract, abi=attr.abi)

        else:
            # NOTE: **Must raise** `AttributeError` if no attribute found, so that method bubbles up
            raise AttributeError(
                f"Method {attr} not a registered accessory method or event"
            )

    def install(self, bot):
        """
        Dynamically maintain the set of all accessories installed for ``self``.

        Manages internal cache of an instance ``self`` of this class.
        """
        from silverback.types import TaskType

        async def load_purses_by_accessory(snapshot):
            df = self.contract.AccessoryUpdated.query(
                "method,old_accessory,new_accessory"
            )
            self._update_cache_from_logs(*df)

        load_purses_by_accessory.__name__ = (
            f"purse:main:{load_purses_by_accessory.__name__}"
        )
        bot.broker_task_decorator(TaskType.STARTUP)(load_purses_by_accessory)

        async def update_accessory(log):
            self._update_cache_from_logs(log)

        update_accessory.__name__ = f"purse:main:{update_accessory.__name__}"
        bot.broker_task_decorator(
            TaskType.EVENT_LOG, container=self.contract_AccessoryUpdated
        )(update_accessory)
