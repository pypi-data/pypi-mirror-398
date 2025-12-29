import csv
import pkg_resources

class Power:
    def __init__(self, csv_file, text):
        self.csv_file = pkg_resources.resource_filename(__name__, csv_file)
        self.text = text.lower()

    def load(self):
        words = []
        with open(self.csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                words.append(row)
        return words

    def find(self):
        power_words = self.load()
        text_words = self.text.split()
        category_count = {}

        for t in text_words:
            for w in power_words:
                if w['Word'].lower() == t:
                    category = w['Category']
                    if category in category_count:
                        category_count[category] += 1
                    else:
                        category_count[category] = 1

        return category_count

    def ascii_pie_chart(self, category_count):
        total = sum(category_count.values())
        max_width = 50 

        chart = []
        for category, count in category_count.items():
            bar_length = int((count / total) * max_width)
            bar = '=' * bar_length
            percentage = (count / total) * 100
            chart.append(f"{category:30} | {bar} {percentage:.2f}%")
        
        return "\n".join(chart)
