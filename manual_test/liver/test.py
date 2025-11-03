import random
import re

class liver_metabolism:
    def __init__(self, metabolites):
        self.environment = {'liver': metabolites if metabolites is not None else {}}

    def add_(self, environment_name, name, value):
        if environment_name not in self.environment:
            self.environment[environment_name] = {}
        if name not in self.environment[environment_name]:
            self.environment[environment_name][name] = 0
        self.environment[environment_name][name] = self.environment[environment_name][name] + value

    def del_(self, environment_name, name, value):
        if environment_name not in self.environment:
            raise ValueError(f"No {environment_name}.")
        if name not in self.environment[environment_name] or self.environment[environment_name][name] < value:
            raise ValueError(f"{name} not enough.")
        self.environment[environment_name][name] = self.environment[environment_name][name] - value
        if self.environment[environment_name][name] == 0:
            del self.environment[environment_name][name]

    def exist_(self, environment_name, name):
        if environment_name not in self.environment or name not in self.environment[environment_name]:
            return False
        else:
            return True
    

    def Bilirubin_metabolism(self, speed=1):
        # 1 分子间接胆红素 + 2 分子 UDP-葡萄糖醛酸 → 1 分子结合胆红素
        self.del_('liver', 'indirect bilirubin', 1 * speed)
        self.del_('liver', 'UDP-glucuronic acid', 2 * speed)
        self.add_('liver', 'conjugated bilirubin', 1 * speed)

    def MRP2_transporter(self, speed=1):
        # 结合胆红素通过 MRP2 转运蛋白，从肝细胞泌入胆小管
        self.del_('liver', 'conjugated bilirubin', 1 * speed)
        self.add_('Bile ductules', 'conjugated bilirubin', 1 * speed)


    def FA_beta_oxidation(self, speed=1):
        # 1Fatty acid  (Cn​) ⟶ n/2​Acetyl-CoA + (n/2​−1)FADH2 ​+ (n/2​​−1)NADH
        pattern = re.compile(r"^FA-C(\d+)$")
        FA_Cn_list = []
        for k in self.environment.keys():
            match = pattern.match(k)
            if match:
                n = int(match.group(1))  # 提取数字部分
                FA_Cn_list.append((k, n))
        for FA_name, Cn in FA_Cn_list:
            self.del_('liver', FA_name, 1 * speed)
            self.add_('liver', 'Acetyl-CoA', n//2 * speed)
            self.add_('liver', 'FADH2', (n//2-1) * speed)
            self.add_('liver', 'NADH', (n//2-1) * speed)

    def Ketone_body_metabolism(self, speed=1):
        # 1Fatty acid (Cn​)⟶n/4 ​Ketone bodies (乙酰乙酸、beta-羟丁酸、丙酮)
        pattern = re.compile(r"^FA-C(\d+)$")
        FA_Cn_list = []
        for k in self.environment.keys():
            match = pattern.match(k)
            if match:
                n = int(match.group(1))  # 提取数字部分
                FA_Cn_list.append((k, n))
        for FA_name, Cn in FA_Cn_list:
            self.del_('liver', FA_name, 1 * speed)
            self.add_('liver', 'ketone bodies', n//4 * speed)

    def Cholesterol_synthesis(self, speed=1):
        # 18Acetyl−CoA+16NADPH+36ATP⟶1Cholesterol(C27​)
        self.del_('liver', 'acetyl-CoA', 18 * speed)
        self.del_('liver', 'NADPH', 16 * speed)
        self.del_('liver', 'ATP', 36 * speed)
        self.add_('liver', 'cholesterol-C27', 1 * speed)

    def Steroid_synthesis(self, speed=1):
        # 2FPP(C15)⟶Squalene(C30)⟶Lanosterol(C30)⟶Cholesterol(C27)
        self.del_('liver', 'FPP-C15', 2 * speed)
        self.add_('liver', 'cholesterol-C27', 1 * speed)

    def TAG_metabolism(self, speed=1):
        # 1 分子甘油-3-磷酸 + 3 分子脂酰-CoA → 1 分子甘油三酯 (TAG)
        self.del_('liver', 'G3P', 1 * speed)
        self.del_('liver', 'acyl-CoA', 3 * speed)
        self.add_('liver', 'TAG', 1 * speed)

    def Galactose_metabolism(self, speed=1):
        # 半乳糖代谢：1 分子半乳糖 → 1 分子葡萄糖-6-磷酸
        self.del_('liver', 'galactose', 1 * speed)
        self.add_('liver', 'G6P', 1 * speed)

    def Fructose_metabolism(self, speed=1):
        # 果糖代谢：1Fructose→1DHAP+1G3P
        self.del_('liver', 'fructose', 1 * speed)
        self.add_('liver', 'DHAP', 1 * speed)
        self.add_('liver', 'G3P', 1 * speed)

    def Glycolysis(self, speed=1):
        # 糖酵解：1G6P+2NAD++3ADP+3Pi⟶2Pyruvate丙酮酸+2NADH+3ATP+2H2​O+2H+
        self.del_('liver', 'G6P', 1 * speed)
        self.del_('liver', 'NAD+', 2 * speed)
        self.del_('liver', 'ADP', 3 * speed)
        self.del_('liver', 'Pi', 3 * speed)
        self.add_('liver', 'pyruvate', 2 * speed)
        self.add_('liver', 'NADH', 2 * speed)
        self.add_('liver', 'ATP', 3 * speed)
        self.add_('liver', 'H2O', 2 * speed)
        self.add_('liver', 'H+', 2 * speed)

    def Glycogen_synthesis(self, speed=1):
        # 糖原合成：Glucose−6−P+UTP+Glycogen(n)​⟶Glycogen(n+1)​+UDP+2Pi
        pattern = re.compile(r"^glycogen-(\d+)$")
        glycogen_n_list = []
        for k in self.environment.keys():
            match = pattern.match(k)
            if match:
                n = int(match.group(1))  # 提取数字部分
                glycogen_n_list.append((k, n))
        for glycogen_name, n in glycogen_n_list:
            self.del_('liver', 'G6P', 1 * speed)
            self.del_('liver', 'UTP', 1 * speed)
            self.del_('liver', glycogen_name, 1 * speed)
            self.add_('liver', f'glycogen-{n+1}', 1 * speed)
            self.add_('liver', 'UDP', 1 * speed)
            self.add_('liver', 'Pi', 2 * speed)

    def Glycogen_metabolism(self, speed=1):
        # ?
        # 糖原代谢
        # 1G6P+H2​O⟶1Glucose+Pi；
        self.del_('liver', 'G6P', 1 * speed)
        self.del_('liver', 'H2O', 1 * speed)
        self.add_('liver', 'glucose', 1 * speed)
        self.add_('liver', 'Pi', 1 * speed)
        # 1Glycogen+1Pi⟶1Glucose-1-P
        self.del_('liver', 'glycogen', 1 * speed)
        self.del_('liver', 'Pi', 1 * speed)
        self.add_('liver', 'G1P', 1 * speed)

    def Gluconeogenesis_1(self, speed=1):
        # 糖异生：2 丙酮酸 (3C + 3C) → 1 G6P (6C)；
        self.del_('liver', 'pyruvate', 2 * speed)
        self.add_('liver', 'G6P', 1 * speed)

    def Gluconeogenesis_2(self, speed=1):
        # 糖异生：2 乳酸 (3C + 3C) → 2 丙酮酸 → 1 G6P；
        self.del_('liver', 'lactic acid', 2 * speed)
        self.add_('liver', 'G6P', 1 * speed)
        




    



if __name__ == '__main__':
    metabolities = {
        'indirect bilirubin': 1,
        'UDP-glucuronic acid': 2
    }
    liver = liver_metabolism(metabolities)

    # liver.Bilirubin_metabolism()
    # print(liver.environment)
    # liver.MRP2_transporter()
    # print(liver.environment)

    while(True):
        work_flag = False
        if liver.exist_('liver', 'indirect bilirubin'):
            liver.Bilirubin_metabolism()
            work_flag = True
        if liver.exist_('liver', 'conjugated bilirubin'):
            liver.MRP2_transporter()
            work_flag = True
        
        if work_flag == False:
            break
    
    print(liver.environment)
