# format_currency
from babel.numbers import format_decimal
from decimal import Decimal


class NumFmt:
    sufixes = ["", "K", "L", "Cr"]
    sci_expr = [1e0, 1e3, 1e5, 1e7, 1e12, 1e15, 1e18, 1e21, 1e24, 1e27,
                1e30, 1e33, 1e36, 1e39, 1e42, 1e45, 1e48, 1e51, 1e54, 1e57,
                1e60, 1e63, 1e66, 1e69, 1e72, 1e75, 1e78, 1e81, 1e84, 1e87,
                1e90, 1e93, 1e96, 1e99, 1e102, 1e105, 1e108, 1e111, 1e114, 1e117,
                1e120, 1e123, 1e126, 1e129, 1e132, 1e135, 1e138, 1e141, 1e144, 1e147,
                1e150, 1e153, 1e156, 1e159, 1e162, 1e165, 1e168, 1e171, 1e174, 1e177]

    def __init__(self, currency=False, decimals=0, compact=False, absolute=False):
        self.currency = currency
        self.decimals = decimals
        self.compact = compact
        self.absolute = absolute

    def fmt(self, value):
        if self.absolute:
            value = abs(value)

        sufix = ''

        if self.compact:
            value, sufix = self._convert(value)

        if self.currency:
            # output = format_currency(value, 'INR', u'₹ #,##,##0', locale="en_IN", decimal_quantization=False).replace(u'\xa0', u' ') + sufix
            output = format_decimal(self._round_num(value), format=u'₹ #,##,##0', decimal_quantization=False).replace(u'\xa0', u' ') + sufix
        else:
            output = format_decimal(self._round_num(value), format=u'#,##,##0', decimal_quantization=False).replace(u'\xa0', u' ') + sufix
        return output

    def _round_num(self, n):
        n = Decimal(n)
        return n.to_integral() if n == n.to_integral() else round(n.normalize(), self.decimals)

    def _convert(self, n):
        minus_buff = n
        n = abs(n)
        for x in range(len(self.sci_expr)):
            try:
                if n >= self.sci_expr[x] and n < self.sci_expr[x+1]:
                    sufix = self.sufixes[x]
                    if n >= 1e3:
                        # num = str(self._round_num(n/self.sci_expr[x], decimal=self.decimals))
                        num = self._round_num(n/self.sci_expr[x])
                    else:
                        # num = str(n)
                        num = n
                    return ((num if minus_buff > 0 else -1*num), sufix)
                    # return num + sufix if minus_buff > 0 else "-" + num + sufix
            except IndexError:
                print("You've reached the end")
