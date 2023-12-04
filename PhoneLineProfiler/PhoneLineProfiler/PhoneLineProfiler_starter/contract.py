
import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call

# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class MTMContract(Contract):
    """ A Month to Month Contract for a phone line

    === Public Attributes ===
    all from Contract class
    >>> contract = MTMContract(datetime.date(2023, 1, 1))
    >>> bill = Bill()
    >>> contract.new_month(2, 2023, bill)
    >>> contract.start
    datetime.date(2023, 1, 1)
    >>> contract.bill is bill
    True
    >>> contract.cancel_contract()
    50.0
    """
    def __init__(self, start: datetime.date) -> None:
        Contract.__init__(self, start)

    def cancel_contract(self) -> float:
        # copy of same method from contract class
        self.start = None
        return self.bill.get_cost()

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        # set the bill object
        self.bill = bill
        # add the monthly cost
        self.bill.add_fixed_cost(MTM_MONTHLY_FEE)
        # set the rates
        self.bill.set_rates('MTM', MTM_MINS_COST)


class TermContract(Contract):
    """ A Term Contract for a phone line

    === Public Attributes ===
    end:
         end date for the contract
    freeM:
         free minutes given to customer
    expire:
         indicates if contract is expired
    >>> start_date = datetime.date(2022, 1, 1)
    >>> end_date = datetime.date(2022, 12, 31)
    >>> bill = Bill()
    >>> contract = TermContract(start_date, end_date)
    >>> contract.new_month(1, 2022, bill)
    >>> contract.FREE_MINUTES
    100
    >>> contract.cancel_contract()
    20.0
    >>> contract.expire
    True
    """
    end: datetime.date
    FREE: int
    expire: bool

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        Contract.__init__(self, start)
        self.end = end
        self.FREE = TERM_MINS
        self.expire = False

    def cancel_contract(self) -> float:
        # Check if contract has already been cancelled
        if self.start is None:
            return 0.0
        # If not cancelled, cancel it
        self.start = None
        # If expired return total minus deposit
        if self.expire:
            return self.bill.get_cost() - TERM_DEPOSIT
        # Otherwise return total
        else:
            return self.bill.get_cost()

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        # Declare the bill, rates and free mins
        self.bill = bill
        self.bill.set_rates('TERM', TERM_MINS_COST)
        self.FREE = TERM_MINS

        # Check if there is start date
        if self.start is not None:
            # If the years match, add fixed cost
            if self.start.year == year and self.start.month == month:
                self.bill.add_fixed_cost(TERM_DEPOSIT + TERM_MONTHLY_FEE)
            # Otherwise only add monthly fee
            else:
                self.bill.add_fixed_cost(TERM_MONTHLY_FEE)
            # If end date is after given year, it is expired
            if self.end.month > month and self.end.year == year:
                self.expire = True

    def bill_call(self, call: Call) -> None:
        # Find duration of call in minutes
        duration = ceil(call.duration / 60.00)

        # If there are free minutes left, use them
        if self.FREE >= duration:
            self.FREE -= duration
            self.bill.add_free_minutes(duration)
        # If there are not enough free minutes, add remaining free
        # minutes bill and bill the remaining duration
        else:
            self.bill.add_free_minutes(self.FREE)
            duration -= self.FREE
            self.FREE = 0
            self.bill.add_billed_minutes(duration)


class PrepaidContract(Contract):
    """ A Prepaid Contract for a phone line

    === Public Attributes ===
    balance:
         the amount that the customer owes
    >>> prepaid = PrepaidContract("John", 100.12)
    >>> prepaid.balance
    -100.12
    >>> prepaid.cancel_contract()
    0
    """
    balance: float

    def __init__(self, start: datetime.time, balance: float) -> None:
        Contract.__init__(self, start)
        self.balance = -balance

    def cancel_contract(self) -> float:
        # Check if there is a bill
        if self.bill is None:
            return 0
        # Otherwise get the bill
        cost = self.bill.get_cost()
        # If it is 0 or below, return 0
        if cost <= 0:
            return 0
        # Otherwise return cost
        self.start = None
        return cost

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        # If self.start is none, return without anything
        if self.start is None:
            return
        # If is it not none, check if bill is not none
        if self.bill is not None:
            # This is code based on the tasks given in assignment
            self.balance = self.bill.get_cost()
            if self.balance > -10:
                self.balance = -25
        # Set the bill
        self.bill = bill
        # Set the rates
        self.bill.set_rates('PREPAID', PREPAID_MINS_COST)
        # Add fixed costs
        self.bill.add_fixed_cost(self.balance)


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
