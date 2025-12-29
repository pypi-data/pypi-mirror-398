import pandas as pd
from typing import List, Union
import datetime
from collections import defaultdict
from bisect import bisect_left


class Payment:
    def __init__(self, idx, dt, amt):
        self.idx = idx
        self.dt = dt
        self.amt = amt
        self.resolved_amt = 0
        self.unresolved_amt = amt
        self.bill_ar = []
        self.status = ''
        self.comment = ''

    def get_status(self):
        if self.resolved_amt == 0:
            self.status = "Unresolved"
        elif self.unresolved_amt == 0:
            self.status = "Resolved"
        else:
            self.status = "Partially Resolved"
        return self.status

    def get_comment(self):
        if not self.status:
            self.get_status()
        if self.status == "Unresolved":
            self.comment = ''
            return
        if len(self.bill_ar) == 1:
            b = self.bill_ar[0]
            self.comment = f"Paid {b['paid_amt']} for bill dated " + \
                           f"{b['obj'].dt.strftime('%d-%m-%Y')} and id (" + \
                           f"{b['obj'].idx})"
        else:
            self.comment = f"Paid for {len(self.bill_ar)} bills - "
            for b in self.bill_ar:
                self.comment += f"Paid {b['paid_amt']} for bill dated " + \
                                f"{b['obj'].dt.strftime('%d-%m-%Y')} " + \
                                f"and id ({b['obj'].idx})"

    def get_row(self):
        self.get_status()
        self.get_comment()
        return [self.idx, self.dt, self.amt, self.status, self.comment]


class Bill:
    def __init__(self, idx, dt, amt):
        self.idx = idx
        self.dt = dt
        self.amt = amt
        self.paid_amt = 0
        self.unpaid_amt = amt
        self.discount = 0
        self.pymt_ar = []
        self.status = ''
        self.comment = ''

    def get_status(self):
        if self.paid_amt == 0:
            self.status = "Unpaid"
        elif self.unpaid_amt == 0 and self.discount == 0:
            self.status = "Paid"
        elif self.unpaid_amt == 0 and self.discount > 0:
            self.status = "Discounted Paid"
        else:
            self.status = "Partially Paid"
        return self.status

    def check_exact_match(self, amt):
        return self.amt == amt

    def check_disc_match(self, amt, disc_ar):
        for disc in disc_ar:
            disc_amt = self.amt * ((100 - disc) / 100)
            if amt - 1 <= disc_amt <= amt + 1:
                return {"match": True, "disc": disc, "round_amt": amt}
        return {"match": False}

    def provide_discount_and_settle(self, disc, round_amt, pymt):
        self.unpaid_amt = round_amt
        self.discount = disc
        self.settle(pymt)

    def settle(self, pymt: Payment):
        if pymt.unresolved_amt == 0 or self.unpaid_amt == 0:
            return
        if pymt.unresolved_amt >= self.unpaid_amt:
            amt_used = self.unpaid_amt
        else:
            amt_used = pymt.unresolved_amt
        self.paid_amt += amt_used
        self.unpaid_amt -= amt_used
        pymt.resolved_amt += amt_used
        pymt.unresolved_amt -= amt_used
        self.pymt_ar.append({"obj": pymt, "paid_amt": amt_used})
        pymt.bill_ar.append({"obj": self, "paid_amt": amt_used})

    def get_comment(self):
        if not self.status:
            self.get_status()
        if self.status == "Unpaid":
            self.comment = ''
            return
        if self.discount > 0:
            pidx = self.pymt_ar[0]["obj"].idx
            p = self.pymt_ar[0]
            self.comment = f"Paid {p['paid_amt']} on " + \
                           f"{p['obj'].dt.strftime('%d-%m-%Y')} with " + \
                           f"discount of {self.discount} % and id ({pidx})"
            return
        if len(self.pymt_ar) == 1:
            p = self.pymt_ar[0]
            self.comment = f"Paid {p['paid_amt']} on " + \
                           (f"{p['obj'].dt.strftime('%d-%m-%Y')} and id ("
                            f"{p['obj'].idx})")
        else:
            self.comment = f"Paid in {len(self.pymt_ar)} installments - "
            for p in self.pymt_ar:
                self.comment += f"Paid {p['paid_amt']} on " + \
                                (f"{p['obj'].dt.strftime('%d-%m-%Y')} and id ("
                                 f"{p['obj'].idx})")

    def get_row(self):
        self.get_status()
        self.get_comment()
        return [self.idx, self.dt, self.amt, self.status, self.comment]


class ReconcilePayment:
    def __init__(self, bill_ar: List[Bill], pymt_ar: List[Payment],
                 disc_ar: List[Union[int, float]]):
        self.bill_dtl_df: pd.DataFrame = pd.DataFrame()
        self.pymt_dtl_df: pd.DataFrame = pd.DataFrame()
        self.bill_ar = bill_ar
        self.pymt_ar = pymt_ar
        self.disc_ar = disc_ar
        self.max_combination_rows = 1000
        self.max_combination_days = 100
        self.max_distribute_rows = 1000

    def get_unpaid_bills_on_or_before(self, dt):
        return [x for x in self.bill_ar if x.dt <= dt and x.unpaid_amt > 0]

    def get_unpaid_bills(self):
        return [x for x in self.bill_ar if x.unpaid_amt > 0]

    def get_unresolved_payments(self):
        return [x for x in self.pymt_ar if x.unresolved_amt > 0]

    def get_unresolved_payments_on_or_after(self, dt):
        return [x for x in self.pymt_ar if x.unresolved_amt > 0 and x.dt >= dt]

    def match_exact_values(self):
        d_bill = defaultdict(list)
        for bill in self.bill_ar:
            d_bill[bill.unpaid_amt].append(bill)
        for pymt in self.get_unresolved_payments():
            for bill in d_bill[pymt.amt]:
                if bill.dt <= pymt.dt and bill.unpaid_amt > 0:
                    bill.settle(pymt)

    def distribute_payment(self):
        if (self.max_distribute_rows < len(self.pymt_ar) or
            self.max_distribute_rows) < len(self.bill_ar):
            print(
                f"Not performing distribute as length of dataframe exceeds"
                f"{self.max_distribute_rows}. Pass parameter "
                f"max_distribute_rows= to overrde this number")
            return
        for pymt in self.get_unresolved_payments():
            for bill in self.get_unpaid_bills_on_or_before(pymt.dt):
                bill.settle(pymt)
                if pymt.unresolved_amt == 0:
                    break

    def match_discounted_values(self):
        d_bill = defaultdict(list)
        for bill in self.bill_ar:
            d_bill[bill.unpaid_amt].append(bill)
        amt_ar_sorted = sorted(d_bill.keys())
        max_mltplr = (100 - min(self.disc_ar)) / 100
        min_mltplr = (100 - max(self.disc_ar)) / 100
        for pymt in self.get_unresolved_payments():
            strt_idx = bisect_left(amt_ar_sorted,
                                   int(pymt.amt * min_mltplr) - 1)
            end_idx = bisect_left(amt_ar_sorted,
                                  int(pymt.amt * max_mltplr) + 1)
            for amt in amt_ar_sorted[strt_idx:end_idx + 1]:
                for bill in d_bill[amt]:
                    if bill.dt <= pymt.dt and bill.unpaid_amt > 0:
                        disc_mtch = bill.check_disc_match(pymt.amt,
                                                          self.disc_ar)
                        if disc_mtch["match"]:
                            bill.provide_discount_and_settle(disc_mtch["disc"],
                                                             disc_mtch[
                                                                 "round_amt"],
                                                             pymt)

    def match_combined_payments(self):
        if (len(self.pymt_ar) > self.max_combination_rows or len(self.bill_ar)
                > self.max_combination_rows):
            print(f"Not performing combined payments as dataframe size "
                  f"exceeds {self.max_combination_rows}. To perform combined "
                  f"payments pass max_combination_rows= parameter when calling "
                  f"reconcile")
            return
        d_pymt = defaultdict(list)
        for pymt in self.pymt_ar:
            d_pymt[pymt.unresolved_amt].append(pymt)
        d_amt_ar = sorted(d_pymt.keys())
        # One bill being paid in more than 1 payment
        for i, bill in enumerate(self.get_unpaid_bills()):
            print(i)
            max_dt = bill.dt + datetime.timedelta(
                days=self.max_combination_days)
            amt_ar = d_amt_ar[:bisect_left(d_amt_ar, bill.amt) + 1]
            pymt_ar = [y for x in amt_ar for y in d_pymt[x] if y.dt >= bill.dt
                       and y.dt <= max_dt and y.unresolved_amt > 0]
            mtch = find_combinations_with_target_sum(pymt_ar, bill.unpaid_amt,
                                                     "unresolved_amt")
            if mtch:
                for pymt in mtch[0]:
                    bill.settle(pymt)

        # One payment being done for more than 1 bills
        for pymt in self.get_unresolved_payments():
            bill_ar = self.get_unpaid_bills_on_or_before(pymt.dt)
            mtch = find_combinations_with_target_sum(bill_ar,
                                                     pymt.unresolved_amt,
                                                     "unpaid_amt")
            if mtch:
                for bill in mtch[0]:
                    bill.settle(pymt)

    def reconcile(self):
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "Getting matches for exact values")
        self.match_exact_values()
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "Getting matches for discounted values")
        self.match_discounted_values()
        print("Getting combined payments")
        self.match_combined_payments()
        print("Getting distributed payments")
        self.distribute_payment()
        self.bill_dtl_df = pd.DataFrame([x.get_row() for x in self.bill_ar],
                                        columns=[
                                            "ID", "Bill Date", "Bill Amount",
                                            "Status", "Comment"])
        self.pymt_dtl_df = pd.DataFrame([x.get_row() for x in self.pymt_ar],
                                        columns=[
                                            "ID", "Payment Date",
                                            "Payment Amount",
                                            "Status", "Comment"])

    def to_excel(self, out_fl):
        self.bill_dtl_df.to_excel(out_fl, startcol=1, index=False)
        with pd.ExcelWriter(out_fl, mode="a", if_sheet_exists='overlay') as f:
            self.pymt_dtl_df.to_excel(f, startcol=8, index=False)


def find_combinations_with_target_sum(amt_obj_ar, target_amt, pmt_attrib_nm):
    result = []

    def backtrack(start, current_combination, current_sum):
        if current_sum == target_amt:
            result.append(list(current_combination))
            return
        if current_sum > target_amt:
            return

        for i in range(start, len(amt_obj_ar)):
            current_combination.append(amt_obj_ar[i])
            backtrack(i + 1, current_combination,
                      current_sum + getattr(amt_obj_ar[i], pmt_attrib_nm))
            if len(result) > 0:
                return
            current_combination.pop()

    backtrack(0, [], 0)
    return result


def reconcile_payment(bill_df: pd.DataFrame, pymt_df: pd.DataFrame,
                      bill_dt_col: str, bill_amt_col: str, pymt_dt_col: str,
                      pymt_amt_col: str,
                      disc_ar: List[Union[int, float]],
                      max_combination_rows: int = 1000,
                      max_combination_days: int = 30,
                      max_distribute_rows: int = 1000) -> ReconcilePayment:
    bill_ar = [Bill(i, x[0], x[1]) for i, x in enumerate(sorted(
        bill_df[[bill_dt_col, bill_amt_col]].values.tolist()), 1)]
    pymt_ar = [Payment(i, x[0], x[1]) for i, x in enumerate(sorted(
        pymt_df[[pymt_dt_col, pymt_amt_col]].values.tolist()), 1)]
    disc_ar = disc_ar
    recon = ReconcilePayment(bill_ar, pymt_ar, disc_ar)
    recon.max_combination_rows = max_combination_rows
    recon.max_combination_days = max_combination_days
    recon.max_distribute_rows = max_distribute_rows
    recon.reconcile()
    return recon
