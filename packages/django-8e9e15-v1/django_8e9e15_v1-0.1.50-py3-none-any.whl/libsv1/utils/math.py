from datetime import datetime
import math
from decimal import Decimal


class MathUtils:
    @staticmethod
    def round_down(value, decimal_places):
        multiplier = 10 ** decimal_places
        return math.floor(value * multiplier) / multiplier

    @staticmethod
    def round_up(value, decimal_places):
        multiplier = 10 ** decimal_places
        return math.ceil(value * multiplier) / multiplier

    @staticmethod
    def increase_by_percent(value, pct, value_round=None):
        if value is None:
            return None
        if not pct:
            return value
        value = float(Decimal(value) * (Decimal(1) + round(Decimal(pct) / Decimal(100), 3)))
        if value_round is not None:
            return round(value, value_round)
        return value

    @staticmethod
    def decrease_by_percent(value, pct, value_round=None):
        if value is None:
            return None
        if not pct:
            return value
        value = float(Decimal(value) * (Decimal(1) - round(Decimal(pct) / Decimal(100), 3)))
        if value_round is not None:
            return round(value, value_round)
        return value

    @staticmethod
    def get_percent(start, end, pct_round):
        if start == 0:
            return 100
        elif end == 0:
            return -100
        start = Decimal(str(start))
        end = Decimal(str(end))
        pct = ((end - start) / start) * 100
        pct = MathRepository.half_round(pct, 1) if pct_round == 0.5 else round(float(pct), int(pct_round))
        pct = int(pct) if pct_round == 0 else pct
        return pct

    @staticmethod
    def get_percent_true_result(true_total, total, round_places=2):
        if not true_total:
            return 0
        if not total:
            return 100
        true_total = Decimal(str(true_total))
        total = Decimal(str(total))
        result = round((true_total / (total / 100)), round_places)
        return 100 if result > 100 else result

    @staticmethod
    def half_round(number, round_places=3):
        integer_part = math.floor(number)
        fractional_part = Decimal(str(number)) - Decimal(str(integer_part))
        if fractional_part < 0.3:
            return round(float(integer_part), round_places)
        elif fractional_part < 0.8:
            return round(float(integer_part + 0.5), round_places)
        else:
            return round(float(Decimal(str(integer_part)) + Decimal(str(1))), round_places)

    @staticmethod
    def get_distance_from_degrees(lat1, lng1, lat2, lng2):
        delta_lat = abs(lat2 - lat1)
        delta_lng = abs(lng2 - lng1)
        lat_km = delta_lat * 111.32
        avg_lat = (lat1 + lat2) / 2
        lng_km = delta_lng * 111.32 * math.cos(math.radians(avg_lat))
        distance = math.sqrt(lat_km ** 2 + lng_km ** 2)
        return distance

    @staticmethod
    def convert_degrees_to_distance(degrees_distance, lat=None):
        if not lat is None:
            distance = degrees_distance * 111.32 * math.cos(math.radians(lat))
        else:
            distance = degrees_distance * 111.32
        return distance

    @staticmethod
    def age(birthday_at):
        if not birthday_at:
            return None
        try:
            birthday = datetime.strptime(birthday_at, '%Y-%m-%d')
            today = datetime.now()
            age_years = today.year - birthday.year
            if (today.month, today.day) < (birthday.month, birthday.day):
                age_years -= 1
            return age_years
        except ValueError:
            return None

    @staticmethod
    def array_median(array):
        count = len(array)
        if count == 0:
            return 0
        sorted_array = sorted(array)
        middle_index = count // 2
        if count % 2 == 0:
            median = (sorted_array[middle_index - 1] + sorted_array[middle_index]) / 2
        else:
            median = sorted_array[middle_index]

        return int(median)

    @staticmethod
    def calculate_median(values):
        filtered_values = [v for v in values if isinstance(v, (int, float)) and v >= 0]
        return MathRepository.array_median(filtered_values)

    @staticmethod
    def float_to_string(value):
        formatted_str = "{:.10f}".format(float(value))
        no_trailing_zeros = formatted_str.rstrip('0')
        final_str = no_trailing_zeros.rstrip('.')
        if final_str == "" or final_str == "-":
            return "0"
        if final_str == "-0":
            return "0"
        return final_str

    @staticmethod
    def round_by_last_price(price, last_price=None):
        if not price:
            return 0
        if last_price:
            return round(price, MathRepository.get_count_num_after_point(last_price))
        return float(price)

    @staticmethod
    def get_count_num_after_point(value):
        formatted_str = MathRepository.float_to_string(value)
        if '.' in formatted_str:
            return len(formatted_str.split('.', 1)[1])
        else:
            return 0

    @staticmethod
    def cut_by_precision(value=0, precision=0):
        if value is None or value == 0:
            return 0
        if precision is None:
            return value
        if precision <= 0:
            return int(value)

        current_precision = MathRepository.get_count_num_after_point(value)
        if current_precision <= precision:
            return value

        multiplier = 10 ** precision
        truncated_value = math.trunc(value * multiplier)
        return truncated_value / multiplier

    @staticmethod
    def get_precision(values):
        if not isinstance(values, list):
            values = [values]
        for i, v in enumerate(values):
            values[i] = MathRepository.get_count_num_after_point(v)
        return max(values)