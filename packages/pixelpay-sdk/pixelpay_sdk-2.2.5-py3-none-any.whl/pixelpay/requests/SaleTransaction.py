from ..base import Helpers
from .AuthTransaction import AuthTransaction


class SaleTransaction(AuthTransaction):
    def __init__(self):
        super().__init__()

        self.installment_type: str = None
        """Transaction installment type"""

        self.installment_months: str = None
        """Transaction installment value"""

        self.points_redeem_amount: str = None
        """Transaction total points redeem amount"""

    def setInstallment(self, months: int, financing_type: str):
        """Set Installment service values to transaction

        Args:
            months (int): installment months
            financing_type (str): installment type
        """
        self.installment_months = str(months)
        self.installment_type = financing_type

    def withPointsRedeemAmount(self, amount: float):
        """Set transaction points redeem amount

        Args:
            amount (float): points redeem amount
        """
        self.points_redeem_amount = Helpers.parseAmount(amount)
