import csv
import random
import datetime
import os

downloads_dir = os.path.expanduser("~/Downloads")
file_path = os.path.join(downloads_dir, "heparadar_500_patients.csv")

with open(file_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["mrn", "age", "sex", "date", "ast", "alt", "plt", "bilirubin", "albumin", "anti_hcv", "hcv_rna"])
    
    for i in range(1, 501):
        mrn = f"BIG{i:03d}"
        age = random.randint(18, 80)
        sex = random.choice(["male", "female"])
        date = (datetime.date.today() - datetime.timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
        
        # 80% normal, 20% abnormal
        if random.random() < 0.8:
            ast = random.randint(15, 35)
            alt = random.randint(10, 35)
            plt = random.randint(150, 400)
            bilirubin = round(random.uniform(0.3, 1.2), 1)
            albumin = round(random.uniform(3.5, 5.0), 1)
        else:
            ast = random.randint(40, 200)
            alt = random.randint(40, 250)
            plt = random.randint(50, 140) # thrombocytopenia
            bilirubin = round(random.uniform(1.3, 3.5), 1)
            albumin = round(random.uniform(2.5, 3.4), 1)
            
        anti_hcv = ""
        hcv_rna = ""
        
        # assign hcv tests
        if random.random() < 0.3:
            # tested for anti_hcv
            anti_val = round(random.uniform(0.01, 20.0), 2)
            anti_hcv = anti_val
            if anti_val > 1.0 and random.random() < 0.7:
                # got RNA test
                if random.random() < 0.8:
                    hcv_rna = random.randint(10000, 5000000)
                else:
                    hcv_rna = 0
                    
        writer.writerow([mrn, age, sex, date, ast, alt, plt, bilirubin, albumin, anti_hcv, hcv_rna])

print(f"Successfully generated {file_path}")
