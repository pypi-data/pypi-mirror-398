"""Provides limited access to the Starling bank API."""
from requests import get, put
from uuid import uuid4
from json import dumps as json_dumps
from base64 import b64decode
from typing import Dict
from datetime import datetime

BASE_URL = "https://api.starlingbank.com/api/v2"
BASE_URL_SANDBOX = "https://api-sandbox.starlingbank.com/api/v2"


"""Build a URL from the API's base URLs."""
def _url(endpoint: str, sandbox: bool = False) -> str:
    if sandbox is True:
        url = BASE_URL_SANDBOX
    else:
        url = BASE_URL
    return "{0}{1}".format(url, endpoint)


"""Representation of a Savings Goal."""
class SavingsGoal:

    def __init__(
        self, auth_headers: Dict, sandbox: bool, account_uid: str
    ) -> None:
        self._auth_headers = auth_headers
        self._sandbox = sandbox
        self._account_uid = account_uid

        self.uid = None
        self.name = None
        self.target_currency = None
        self.target_minor_units = None
        self.total_saved_currency = None
        self.total_saved_minor_units = None

    def update(self, goal: Dict = None) -> None:
        """Update a single savings goals data."""
        if goal is None:
            endpoint = "/account/{0}/savings-goals/{1}".format(
                self._account_uid, self.uid
            )

            response = get(
                _url(endpoint, self._sandbox), headers=self._auth_headers
            )
            response.raise_for_status()
            goal = response.json()

        self.uid = goal.get("savingsGoalUid")
        self.name = goal.get("name")

        target = goal.get("target", {})
        self.target_currency = target.get("currency")
        self.target_minor_units = target.get("minorUnits")

        total_saved = goal.get("totalSaved", {})
        self.total_saved_currency = total_saved.get("currency")
        self.total_saved_minor_units = total_saved.get("minorUnits")

    def deposit(self, deposit_minor_units: int) -> None:
        """Add funds to a savings goal."""
        endpoint = "/account/{0}/savings-goals/{1}/add-money/{2}".format(
            self._account_uid, self.uid, uuid4()
        )

        body = {
            "amount": {
                "currency": self.total_saved_currency,
                "minorUnits": deposit_minor_units,
            }
        }

        response = put(
            _url(endpoint, self._sandbox),
            headers=self._auth_headers,
            data=json_dumps(body),
        )
        response.raise_for_status()

        self.update()

    def withdraw(self, withdraw_minor_units: int) -> None:
        """Withdraw funds from a savings goal."""
        endpoint = "/account/{0}/savings-goals/{1}/withdraw-money/{2}".format(
            self._account_uid, self.uid, uuid4()
        )

        body = {
            "amount": {
                "currency": self.total_saved_currency,
                "minorUnits": withdraw_minor_units,
            }
        }

        response = put(
            _url(endpoint, self._sandbox),
            headers=self._auth_headers,
            data=json_dumps(body),
        )
        response.raise_for_status()

        self.update()

    def get_image(self, filename: str = None) -> None:
        """Download the photo associated with a Savings Goal."""
        if filename is None:
            filename = "{0}.png".format(self.name)

        endpoint = "/account/{0}/savings-goals/{1}/photo".format(
            self._account_uid, self.uid
        )

        response = get(
            _url(endpoint, self._sandbox), headers=self._auth_headers
        )
        response.raise_for_status()

        base64_image = response.json()["base64EncodedPhoto"]
        with open(filename, "wb") as file:
            file.write(b64decode(base64_image))



"""Representation of a Spending Category."""
class SpendingCategory:

    def __init__(
        self, auth_headers: Dict, sandbox: bool, account_uid: str
    ) -> None:
        self._auth_headers = auth_headers
        self._sandbox = sandbox
        self._account_uid = account_uid

        self.month = None
        self.year = None
        self.spending_category = None
        self.net_direction = None
        self.currency = None
        self.total_spent = 0.0
        self.total_received = 0.0
        self.net_spend = 0.0
        self.percentage = 0.0
        self.transaction_count = 0

    def update(self, category: Dict = None, month: str = None, year: str = None) -> None:
        """Update a single spending category data."""
        self.month = month
        self.year = year
        self.spending_category = category.get("spendingCategory")
        self.net_direction = category.get("netDirection")
        self.currency = category.get("currency")
        self.total_spent = category.get("totalSpent")
        self.total_received = category.get("totalReceived")
        self.net_spend = category.get("netSpend")
        self.percentage = category.get("percentage")
        self.transaction_count = category.get("transactionCount")

class Space:

    def __init__(
        self, auth_headers: Dict, sandbox: bool, account_uid: str
    ) -> None:
        self._auth_headers = auth_headers
        self._sandbox = sandbox
        self._account_uid = account_uid

        self.uid = None
        self.name = None
        self.balance = 0.0
        self.card_association_uid = None
        self.space_type = None
        self.active = True

    def update(self, space: Dict = None) -> None:
        """Update a single space's data."""
        self.uid = space.get("spaceUid")
        self.name = space.get("name")
        self.balance = space.get("balance", {}).get("minorUnits", 0.0)
        self.card_association_uid = space.get("cardAssociationUid")
        self.space_type = space.get("spendingSpaceType")
        self.active = (space.get("state", "ACTIVE") == "ACTIVE")

"""Representation of a Starling Account."""
class StarlingAccount:

    def update_account_data(self) -> None:
        """Get basic information for the account."""
        response = get(
            _url(
                "/accounts/{0}/identifiers".format(self._account_uid),
                self._sandbox,
            ),
            headers=self._auth_headers,
        )
        response.raise_for_status()

        response = response.json()

        self.account_identifier = response.get("accountIdentifier")
        self.bank_identifier = response.get("bankIdentifier")
        self.iban = response.get("iban")
        self.bic = response.get("bic")

    def update_balance_data(self) -> None:
        """Get the latest balance information for the account."""
        response = get(
            _url(
                "/accounts/{0}/balance".format(self._account_uid),
                self._sandbox,
            ),
            headers=self._auth_headers,
        )
        response.raise_for_status()

        response = response.json()
        self.cleared_balance = response["clearedBalance"]["minorUnits"]
        self.effective_balance = response["effectiveBalance"]["minorUnits"]
        self.pending_transactions = response["pendingTransactions"][
            "minorUnits"
        ]
        self.accepted_overdraft = response["acceptedOverdraft"]["minorUnits"]

    def update_savings_goal_data(self) -> None:
        """Get the latest savings goal information for the account."""
        response = get(
            _url(
                "/account/{0}/savings-goals".format(self._account_uid),
                self._sandbox,
            ),
            headers=self._auth_headers,
        )
        response.raise_for_status()

        response = response.json()
        response_savings_goals = response.get("savingsGoalList", {})

        returned_uids = []

        # New / Update
        for goal in response_savings_goals:
            uid = goal.get("savingsGoalUid")
            returned_uids.append(uid)

            # Intiialise new _SavingsGoal object if new
            if uid not in self.savings_goals:
                self.savings_goals[uid] = SavingsGoal(
                    self._auth_headers, self._sandbox, self._account_uid
                )

            self.savings_goals[uid].update(goal)

        # Forget about savings goals if the UID isn't returned by Starling
        for uid in list(self.savings_goals):
            if uid not in returned_uids:
                self.savings_goals.pop(uid)
    
    def update_spaces_data(self) -> None:
        """Get the latest spaces information for the account."""
        response = get(
            _url(
                "/account/{0}/spaces".format(self._account_uid),
                self._sandbox,
            ),
            headers=self._auth_headers,
        )
        response.raise_for_status()

        response = response.json()
        response_spaces = response.get("spendingSpaces", {})

        returned_uids = []

        # New / Update
        for space in response_spaces:
            uid = space.get("spaceUid")
            returned_uids.append(uid)

            # Intiialise new _Space object if new
            if uid not in self.spaces:
                self.spaces[uid] = Space(
                    self._auth_headers, self._sandbox, self._account_uid
                )

            self.spaces[uid].update(space)

        # Forget about spaces if the UID isn't returned by Starling
        for uid in list(self.spaces):
            if uid not in returned_uids:
                self.spaces.pop(uid)

    def _set_basic_account_data(self):
        response = get(
            _url("/accounts", self._sandbox), headers=self._auth_headers
        )
        response.raise_for_status()

        response = response.json()

        # Assume there will be only 1 account as this is the case with
        # personal access.
        account = response["accounts"][0]

        self._account_uid = account["accountUid"]
        self.currency = account["currency"]
        self.created_at = account["createdAt"]

    def update_spending_categories_data(self, month: str = None, year: str = None) -> None:
        """Get the spending categories information for the account, default for the latest month."""
        if not month or not year:
            year = str(datetime.now().year)
            month = datetime.now().strftime("%B").upper()  # Converts month to uppercase

        response = get(
            _url(
                "/accounts/{0}/spending-insights/spending-category?year={1}&month={2}".format(self._account_uid,
                                                                                              year, month),
                self._sandbox,
            ),
            headers=self._auth_headers,
        )
        response.raise_for_status()

        response = response.json()
        response_spending_categories = response.get("breakdown", {})

        returned_categories = []

        # Initialize spending categories
        for category in response_spending_categories:
            category_name = category.get("spendingCategory")
            returned_categories.append(category_name)

            # Initialize new SpendingCategory object if new
            if category_name not in self.spending_categories:
                self.spending_categories[category_name] = SpendingCategory(self._auth_headers, self._sandbox,
                                                                           self._account_uid)

            # Update the spending category data
            self.spending_categories[category_name].update(category, month, year)

        # Set values to zero if category not returned
        for category_name in self.spending_categories:
            if category_name not in returned_categories:
                self.spending_categories[category_name].update({
                    "totalSpent": 0.0,
                    "totalReceived": 0.0,
                    "netSpend": 0.0,
                    "percentage": 0.0,
                    "transactionCount": 0,
                })

    def __init__(
        self, api_token: str, update: bool = False, sandbox: bool = False
    ) -> None:
        """Call to initialise a StarlingAccount object."""
        self._api_token = api_token
        self._sandbox = sandbox
        self._auth_headers = {
            "Authorization": "Bearer {0}".format(self._api_token),
            "Content-Type": "application/json",
        }
        self._set_basic_account_data()

        # Account Data
        self.account_identifier = None
        self.bank_identifier = None
        self.iban = None
        self.bic = None

        # Balance Data
        self.cleared_balance = None
        self.effective_balance = None
        self.pending_transactions = None
        self.accepted_overdraft = None

        # Savings Goals Data
        self.savings_goals = {}  # type: Dict[str, SavingsGoal]

        # Spending Category Data
        self.spending_categories = {}  # type: Dict[str, SpendingCategory]

        # Spaces data
        self.spaces = {}  # type: Dict[str, Space]

        if update:
            self.update_account_data()
            self.update_balance_data()
            self.update_savings_goal_data()
            self.update_spending_categories_data()
            self.update_spaces_data()
