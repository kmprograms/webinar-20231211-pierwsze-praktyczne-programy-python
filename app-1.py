import logging
import requests
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import Enum

"""
Przeliczanie walut:
Poproś użytkownika o wprowadzenie kwoty w jednej walucie (np. dolarach) i przelicz ją na inną walutę
(np. euro). Możesz dla uproszczenie używac kilku walut.
"""

# >> pip install requests
# pipenv, poetry

# requests
# https://www.python-httpx.org/
# http://api.nbp.pl/api/exchangerates/rates/a/eur/?format=json

# d = requests.get('http://api.nbp.pl/api/exchangerates/rates/a/eur/?format=json').json()
# print(d)
# print(d['table'])
# print(d['rates'][0])

@dataclass  # __init__, __eq__, __hash__, __str__
class Rate:
    no: str
    effectiveDate: str  # effective_date
    mid: Decimal

    def calc_pln_value(self, value: Decimal) -> Decimal:
        return (self.mid * value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Specjalna metoda, ktora definiuje inny sposob tworzenia obiektu (przynajmniej nas interesuje
    # to wykorzystanie)
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> 'Rate':
        # return Rate(data)
        # {'no': '239/A/NBP/2023', 'effectiveDate': '2023-12-11', 'mid': 4.3366}
        data |= {'mid': Decimal(str(data['mid']))}
        return cls(**data)


@dataclass
class NBPData:
    table: str
    code: str
    currency: str
    rates: list[Rate]

    def calc_pln_value(self, value: Decimal) -> Decimal:
        # Sprawdzic czy w liscie jest co najmniej jeden element
        return self.rates[0].calc_pln_value(value)

    @classmethod
    def from_currency(cls, currency: str) -> 'NBPData':
        data = requests.get(f'http://api.nbp.pl/api/exchangerates/rates/a/{currency}/?format=json').json()
        data |= {'rates': [Rate.from_dict(d) for d in data['rates']]}
        return cls(**data)


class Currency(Enum):
    PLN = 'pln',
    EUR = 'eur',
    GBP = 'gbp',
    USD = 'usd'

def convert(value: Decimal, curr_from: Currency, curr_to: Currency = Currency.PLN) -> Decimal:
    currency_from = curr_from.value[0]
    currency_to = curr_to.value[0]

    if currency_to == currency_from:
        return value

    if currency_to == 'pln':
        return NBPData.from_currency(currency_from).calc_pln_value(value)

    if currency_from == 'pln':
        # TODO Dla Ciebie currency_from == 'pln' oraz currency_to jest inna niz pln
        return None

    pln_value_from = NBPData.from_currency(currency_from).calc_pln_value(value)
    pln_value_to = NBPData.from_currency(currency_to).calc_pln_value(Decimal(1))
    return (pln_value_from / pln_value_to).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def main() -> None:
    print('------------------------------- [ 1 ] -------------------------------')
    rate1 = Rate(no='1', effectiveDate='2023', mid=Decimal('12.2'))
    print(rate1)
    print(rate1.calc_pln_value(Decimal('12.3128')))

    print('------------------------------- [ 2 ] -------------------------------')
    d = {'no': '239/A/NBP/2023', 'effectiveDate': '2023-12-11', 'mid': 4.3366}
    rate2 = Rate.from_dict(d)
    print(rate2)

    print('------------------------------- [ 3 ] -------------------------------')
    nbp_data = NBPData.from_currency('gbp')
    print(nbp_data)
    print(nbp_data.calc_pln_value(Decimal('100')))

    print('------------------------------- [ 4 ] -------------------------------')
    print(convert(Decimal('10.0'), Currency.PLN, Currency.PLN))
    print(convert(Decimal('10.0'), Currency.GBP, Currency.PLN))
    print(convert(Decimal('10.0'), Currency.GBP, Currency.EUR))
    print(convert(Decimal('10.0'), Currency.GBP))



if __name__ == '__main__':
    main()