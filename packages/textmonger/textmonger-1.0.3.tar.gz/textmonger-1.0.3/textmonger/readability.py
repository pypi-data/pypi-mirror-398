from tabulate import tabulate
import textstat

class Readability:
    def __init__(self, text):
        self.text = text
    
    def ease(self):
        score = textstat.flesch_reading_ease(self.text)
        if score >= 90:
            level = "Very easy"
        elif score >= 80:
            level = "Easy"
        elif score >= 70:
            level = "Fairly easy"
        elif score >= 60:
            level = "Standard"
        elif score >= 50:
            level = "Fairly difficult"
        elif score >= 30:
            level = "Difficult"
        else:
            level = "Very confusing"
        return ("Reading ease", level)

    def kincaid(self):
        score = textstat.flesch_kincaid_grade(self.text)
        return ("Reading level", f'Grade {score}')

    def smog(self):
        score = textstat.smog_index(self.text)
        return ("Smog index", f'Grade {score}')

    def fog(self):
        score = textstat.gunning_fog(self.text)
        return ("Gunning Fog index", f'Grade {score}')

    def liau(self):
        score = textstat.coleman_liau_index(self.text)
        return ("Coleman-Liau index", f'Grade {score}')

    def automated(self):
        score = textstat.automated_readability_index(self.text)
        return ("Automated Readability index", f'Grade {score}')

    def chall(self):
        score = textstat.dale_chall_readability_score(self.text)
        return ("Dale-Chall Readability score", score)
    
    def standard(self):
        score = textstat.text_standard(self.text)
        return ("Text standard", score)

    def analyze(self):
        results = [
            self.ease(),
            self.kincaid(),
            self.smog(),
            self.fog(),
            self.liau(),
            self.automated(),
            self.chall(),
            self.standard()
        ]
        table = tabulate(results, headers=["Metric", "Score"], tablefmt="grid")
        return table
