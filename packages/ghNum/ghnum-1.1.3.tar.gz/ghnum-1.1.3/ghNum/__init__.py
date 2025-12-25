
import re
from typing import Union, Dict, List

class PersianTextToNumber:
    """
    ghNum: A professional library to convert Persian words to numbers.
    Features: Ordinal numbers, Large scales, Multilingual output, Thousand separators.
    """
    def __init__(self) -> None:
        self._base_numbers = {
            'صفر': 0, 'یک': 1, 'دو': 2, 'سه': 3, 'چهار': 4, 'پنج': 5,
            'شش': 6, 'شیش': 6, 'هفت': 7, 'هشت': 8, 'نه': 9, 'ده': 10,
            'یازده': 11, 'دوازده': 12, 'سیزده': 13, 'چهارده': 14, 'پانزده': 15,
            'شانزده': 16, 'هفده': 17, 'هجده': 18, 'نوزده': 19,
            'بیست': 20, 'سی': 30, 'چهل': 40, 'پنجاه': 50,
            'شصت': 60, 'هفتاد': 70, 'هشتاد': 80, 'نود': 90,
            'صد': 100, 'دویست': 200, 'سیصد': 300, 'چهارصد': 400, 'پانصد': 500,
            'ششصد': 600, 'هفتصد': 700, 'هشتصد': 800, 'نهصد': 900,
        }
        self._scales = {
            'هزار': 1000, 'میلیون': 10**6, 'میلیارد': 10**9,
            'تریلیون': 10**12, 'کوادریلیون': 10**15
        }
        self._ordinal_map = {'اول': 'یک', 'یکم': 'یک', 'نخست': 'یک', 'دوم': 'دو', 'سوم': 'سه'}

    def _normalize(self, text: str) -> str:
        text = text.replace('ي', 'ی').replace('ك', 'ک').replace('‌', ' ')
        return re.sub(r'[^\w\s]', '', text)

    def _to_cardinal(self, word: str) -> str:
        if word in self._ordinal_map: return self._ordinal_map[word]
        
        # اصلاح برای کلماتی که به 'ام' یا 'م' ختم می‌شوند
        if word.endswith('امین'): word = word[:-4]
        elif word.endswith('مین'): word = word[:-3]
        elif word.endswith('ام'): word = word[:-2]
        # در فارسی اعدادی که به ه ختم می‌شوند (مثل پنجاه) وقتی م می‌گیرند، ه حذف نمی‌شود
        elif word.endswith('م'):
            temp = word[:-1]
            if temp in self._base_numbers or temp in self._scales:
                word = temp
        
        # حذف نیم‌فاصله احتمالی باقی‌مانده
        return word.strip()

    def _convert_digits(self, number: int, lang: str, use_separator: bool = False) -> str:
        if use_separator:
            num_str = f"{number:,}"
        else:
            num_str = str(number)
            
        if lang == 'en': return num_str
        
        target = "۰۱۲۳۴۵۶۷۸۹" if lang == 'fa' else "٠١٢٣٤٥٦٧٨٩"
        trans = str.maketrans("0123456789", target)
        return num_str.translate(trans)

    def convert(self, text: str, lang: str = 'en', thousand_separator: bool = False) -> Union[int, str]:
        if not text: return 0
        text = self._normalize(text)
        words = [self._to_cardinal(w) for w in text.split() if w != 'و']
        total_sum, current_chunk = 0, 0
        for word in words:
            if word in self._base_numbers:
                current_chunk += self._base_numbers[word]
            elif word in self._scales:
                if current_chunk == 0: current_chunk = 1
                total_sum += current_chunk * self._scales[word]
                current_chunk = 0
        total_sum += current_chunk
        
        if thousand_separator or lang != 'en':
            return self._convert_digits(total_sum, lang, thousand_separator)
        return total_sum
    
    def convert_list(self, text_list: List[str], lang: str = 'en', thousand_separator: bool = False) -> List[Union[int, str]]:
        return [self.convert(t, lang, thousand_separator) for t in text_list]
