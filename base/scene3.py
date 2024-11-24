from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor


from func import InBlue, OutBlue, MinBlackPass, OutMiddleBlack, InMiddleBlack, Decisive, Stop, LineTrace, SelfPosition, SelfPositionEstimation
from status import Status


# シーンです
# execute"r"です
# 最終的には1つにまとめてもよいが、現状はキャリブレーションシーン、ライントレースシーン、
# ダブルループシーン、デブリリムーバルシーン、スマートキャリーシーンに分割されると思われる

# ここで走行計画を立てて、各種変数を送るため、ここでの与える引数がパラメータとなる
class CalibrationScene(object):
    def __init__(self, state: int, status: Status) -> None:
        self.state = state
        self.min_target = 255
        self.max_target = 0
        self.target = 0
        self.status = status
        #self.black_to_white = OutMiddleBlack()
        self.white_to_black = InMiddleBlack()
        #self.min_black_pass = MinBlackPass()
        self.state_list = [
            Stop(self.status,10),
            Decisive(self.status, 60, 0, side = "right", count = 100),
            Stop(self.status, 50),
            Decisive(self.status, -60, 0, side = "right", count = -200),
            Stop(self.status, 50),
            Decisive(self.status, 75, 0, func = self.white_to_black, type = "midi"),
            #Decisive(self.status, 75, 0, func = self.min_black_pass, type = "midi"),
            Stop(self.status, 55),
        ]


    def executer(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        red = color_sensor.get_raw_color()[0]
        if red < self.status.min_target_red:
            self.status.min_target_red = red
        if red > self.status.max_target_red:
            self.status.max_target_red = red
        self.status.target_red = (self.status.min_target_red + self.status.max_target_red) // 2

        if self.state < len(self.state_list):
            if self.state_list[self.state].check_finish(right_motor, left_motor, color_sensor):
                self.status.reset(right_motor, left_motor)
                self.state += 1
        
        if self.state < len(self.state_list):
            self.state_list[self.state].execute(right_motor, left_motor, color_sensor)
        else:
            pass

# キャリブレーションシーンが終わったことを確認するメソッド
# Trueなら終了、Falseなら続行
    def check_finish(self) -> bool:
        return self.state >= len(self.state_list)





# ライントレースを行うシーン
# 親クラスでキャリブレーションが終わったタイミングで各種値を与えるためgiveメソッドがあります。
class LineTraceScene(object):
    def __init__(self, power: int, state:int, status: Status) -> None:
        # ダブルループのためのフラグ
        self.state = state
        fast = power * 1.3
        slow = power * 0.8
        very_slow = power * 0.6
        self.in_blue = InBlue()
        self.out_blue = OutBlue()

        self.status = status

        self.state_list = [
            LineTrace(self.status, fast, 0.015, 0.5, trace_side = "left", side = "left", count = 3000),  #pの値を0.01下げるとcountを250あげることになる               # 高速
            LineTrace(self.status, slow, 0.15, 0.8, trace_side = "left", side = "left", count = 1300),                 # 低速
            LineTrace(self.status, fast, 0.01, 0.5, trace_side = "left", side = "left", count = 1250),                 # 高速
            LineTrace(self.status, slow, 0.175, 0.8, trace_side = "left", side = "left", count = 1300),                 # 低速
            LineTrace(self.status, power, 0.03, 0.8, trace_side = "left", func = self.in_blue, target = 0.3),          # 中速
            LineTrace(self.status, very_slow, 0.2, 0.5, trace_side = "left", func = self.out_blue, target = 0.1),     # 低速
        ]

        self.first_flag = False
        

    
    def check_finish(self) -> bool:
        return self.state >= len(self.state_list)


    def executer(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if not self.first_flag:
            self.status.reset(right_motor, left_motor)
            self.first_flag = True

        if self.state < len(self.state_list):
            if self.state_list[self.state].check_finish(right_motor, left_motor, color_sensor):
                self.status.reset(right_motor, left_motor)
                self.state += 1
        
        if self.state < len(self.state_list):
            self.state_list[self.state].execute(right_motor, left_motor, color_sensor)
        else:
            right_motor.set_power(0)
            left_motor.set_power(0)
            
       



# ダブルループシーンのクラス
# 上と同様にキャリブレーションで求めた値を利用するため、giveメソッドがあります。
class DoubleLoopScene(object):
    def __init__(self, power: int, state:int, status: Status) -> None:
        self.state = state
        self.in_blue = InBlue()
        self.out_blue = OutBlue()
        self.over_black = MinBlackPass()
        self.out_black = OutMiddleBlack()
        self.in_black = InMiddleBlack()
        slow = power * 0.77
        very_slow = power * 0.5
        self.status = status
        self.state_list = [
            # 1つ目のループに入るため
            Stop(self.status, 70),
            Decisive(self.status, 40, 60, func = self.over_black, type = "min"),
            Decisive(self.status, 40, 50, func = self.out_black, type = "midi"),
            Stop(self.status, 70),

            # 1つ目のループ
            LineTrace(self.status, slow, 0.15, 0.7, trace_side = "right", func = self.in_blue, target = 0.25),
            LineTrace(self.status, very_slow, 0.2, 0.8, trace_side = "right", func = self.out_blue, target = 0.1),

            # 2つ目のループに入るため
            Stop(self.status, 70),
            Decisive(self.status, 67, 40, func = self.over_black, type = "min"),
            Decisive(self.status, 50, 45, func = self.out_black, type = "midi"),
            Stop(self.status, 70),

            # 2つ目のループ
            LineTrace(self.status, slow, 0.2, 0.8, trace_side = "left", func = self.in_blue, target = 0.325),
            LineTrace(self.status, very_slow, 0.2, 0.8, trace_side = "left", func = self.out_blue, target = 0.125),

            # 1つ目のループに入るため
            Stop(self.status, 70),
            Decisive(self.status, 40, 67, func = self.over_black, type = "min"),
            Decisive(self.status, 45, 50, func = self.out_black, type = "midi"),
            Stop(self.status, 70),

            # 1つ目のループ
            LineTrace(self.status, slow, 0.2, 0.8, trace_side = "right", func = self.in_blue, target = 0.3),
            LineTrace(self.status, very_slow, 0.2, 0.8, trace_side = "right", func = self.out_blue, target = 0.125),

            # 抜けるため
            Stop(self.status, 70),
            Decisive(self.status, 50, 45, func = self.over_black, type = "min"),
            Decisive(self.status, 50, 45, func = self.out_black, type = "midi"),
            Stop(self.status, 70),
        ]


    def executer(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if self.state < len(self.state_list):
            if self.state_list[self.state].check_finish(right_motor, left_motor, color_sensor):
                self.status.reset(right_motor, left_motor)
                self.state += 1
        
        if self.state < len(self.state_list):
            self.state_list[self.state].execute(right_motor, left_motor, color_sensor)
        else:
            right_motor.set_power(0)
            left_motor.set_power(0)
            
        #cprint(self.state)
        



    def check_finish(self) -> bool:
        return self.state >= len(self.state_list)
    
#実機の数値はbase_real.pyの値を参照
class Pattern_deburi(object):
    def __init__(self, power: int, state:int, status: Status) -> None:
        self.state = state
        fast = power * 1.4
        slow = power * 0.85
        slow_power = power * 0.77
        very_slow = power * 0.66 #元々0.55
        #self.in_green = InGreen()
        self.in_blue = InBlue()
        self.out_blue = OutBlue()
        self.out_black = OutMiddleBlack()
        self.in_black = InMiddleBlack()
        self.over_black = MinBlackPass()
        self.status = status

        self.state_list = [
            #デブリスタート
            #直進時、乗せるときのpは高く設定してある
            LineTrace(self.status,very_slow, 0.05, 0.5, trace_side = "left", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), #1 

            #青から青(直進)
            SelfPosition(self.status, slow, finish_position_x = 67, finish_position_y = 0, finish_position_a = 0),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.05, 0.5, trace_side = "left", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), 

            #ボトルを動かすための決め打ち
            Decisive(self.status, 60, 40, side = "right", count = 100),
            Stop(self.status, 25),
            Decisive(self.status, -60, -40, side = "right", count = -120),
            Stop(self.status, 25),  #9

            #青から青(右回転の後、直進)
            SelfPosition(self.status, slow, finish_position_x = 10, finish_position_y = 0, finish_position_a = 115),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.15, 0.5, trace_side = "right", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), #13

            #ボトルを動かすための決め打ち
            Decisive(self.status, 60, 40, side = "right", count = 100),
            Stop(self.status, 25),
            Decisive(self.status, -60, -40, side = "right", count = -100),
            Stop(self.status, 25), 

            #青から青(右回転の後、直進)
            SelfPosition(self.status, slow, finish_position_x = 10, finish_position_y = 0, finish_position_a = 115),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.15, 0.5, trace_side = "right", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), 

            #青から青(左回転の後、直進)
            SelfPosition(self.status, slow, finish_position_x = 10, finish_position_y = 0, finish_position_a = -105),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.15, 0.5, trace_side = "right", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), #17

            #青から緑(直進)
            #SelfPosition(self.status, slow, finish_position_x = 67, finish_position_y = 0, finish_position_a = 0),
            #Stop(self.status, 25),
            #LineTrace(self.status,very_slow, 0.05, 0.5, trace_side = "right", func = self.in_blue, target = 0.25),
            #Stop(self.status, 25), 

            #緑から緑(直進)
            SelfPosition(self.status, slow, finish_position_x = 67, finish_position_y = 0, finish_position_a = 0),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.15, 0.5, trace_side = "right", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), 

            #ボトルを動かすための決め打ち
            Decisive(self.status, 40, 60, side = "left", count = 120),
            Stop(self.status, 25),
            Decisive(self.status, -40, -60, side = "left", count = -120),
            Stop(self.status, 25), 
            
            #緑から緑(左回転の後、直進)
            SelfPosition(self.status, slow, finish_position_x = 10, finish_position_y = 0, finish_position_a = -115),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.05, 0.5, trace_side = "right", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), #37
            
            #緑から黄(直進)
            SelfPosition(self.status, slow, finish_position_x = 67, finish_position_y = 0, finish_position_a = 0),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.05, 0.5, trace_side = "right", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), #41

            #黄から黄(左回転の後、直進)
            SelfPosition(self.status, slow, finish_position_x = 10, finish_position_y = 0, finish_position_a = -115),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.15, 0.5, trace_side = "right", func = self.in_blue, target = 0.25),
            Stop(self.status, 25), 

            #ボトルを動かすための決め打ち
            Decisive(self.status, 60, 40, side = "right", count = 100),
            Stop(self.status, 25),
            Decisive(self.status, -60, -40, side = "right", count = -100),
            Stop(self.status, 25), 

            #黄から黄(右回転の後、直進)
            SelfPosition(self.status, slow, finish_position_x = 10, finish_position_y = 0, finish_position_a = 115),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.05, 0.5, trace_side = "left", func = self.in_blue, target = 0.25),
            Stop(self.status, 25),

            #黄から黄(右回転の後、直進)
            SelfPosition(self.status, slow, finish_position_x = 10, finish_position_y = 0, finish_position_a = 100),
            Stop(self.status, 25),
            LineTrace(self.status,very_slow, 0.05, 0.5, trace_side = "left", func = self.in_blue, target = 0.25),
            Stop(self.status, 25),
            
        ]

        self.first_flag = False
        


    """def give_any_value(self, target: int, min_target: int, max_target: int) -> None:
        for state in self.state_list:
            state.give_target(target, min_target, max_target)"""

    
    def check_finish(self) -> bool:
        return self.state >= len(self.state_list)


    def executer(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if not self.first_flag:
            """right_motor.reset_count()
            left_motor.reset_count()"""
            self.status.reset(right_motor,left_motor)
            self.first_flag = True
            
            

        if self.state < len(self.state_list):
            if self.state_list[self.state].check_finish(right_motor, left_motor, color_sensor):
                """right_motor.reset_count()
                left_motor.reset_count()"""
                self.status.reset(right_motor,left_motor)
                print(self.state)
                
                self.state += 1
        
        if self.state < len(self.state_list):
            self.state_list[self.state].execute(right_motor, left_motor, color_sensor)
        else:
            right_motor.set_power(0)
            left_motor.set_power(0)

        #print(self.state)

# xのほうが直進方向の意味（+ が前, - が後ろ）
# yのほうが横方向の意味（+ が右, - が左）
# aのほうが角度の意味（+ が右回り, - が左回り）
# finish_position_x, finish_position_y, は目標地点（count換算）
# count 360 = 1回転
# finish_position_a は目標角度（度数法）(なくてもよい)
class SmartCarryScene(object):
    def __init__(self, power: int, state:int, status: Status) -> None:
        self.state = state
        self.status = status
        self.in_blue = InBlue()
        self.out_blue = OutBlue()
        self.out_black = OutMiddleBlack()
        self.in_black = InMiddleBlack()
        slow_power = power * 0.95 #元々0.8
        very_slow = power * 0.65
        self.state_list = [
            Stop(self.status, 20),
            SelfPosition(self.status, very_slow, finish_position_x = 150, finish_position_y = 0, finish_position_a = 0),
            Stop(self.status, 20),
            LineTrace(self.status, slow_power, 0.2, 0.8, trace_side = "left", side = "left", special = True, count = 85),          # 中速
            Stop(self.status, 20),
            SelfPosition(self.status, slow_power, finish_position_x = 300, finish_position_y = 0, finish_position_a = 100),
            Stop(self.status, 20),
            SelfPosition(self.status, slow_power, finish_position_x = 800, finish_position_y = -300, finish_position_a = 20),
            Stop(self.status, 20),
            #このあたりで決め打ちを入れる
            #お試し
            Decisive(self.status, -60, -120, side = "left", count = -225),
            Stop(self.status, 20),
            SelfPosition(self.status, slow_power, finish_position_x = 100, finish_position_y = -400, finish_position_a = -70),
            Stop(self.status, 20),
            SelfPosition(self.status, slow_power, finish_position_x = 185, finish_position_y = 0, finish_position_a = -130),
            Stop(self.status, 20),
            SelfPosition(self.status, slow_power, finish_position_x = 100, finish_position_y = 0, finish_position_a = -90),
            Stop(self.status, 20),
            #Decisive(self.status, 40, 67, func = self.in_black, type = "min"),
            #SelfPosition(self.status, very_slow, finish_position_x = 1250, finish_position_y = 0, finish_position_a = 0),
            #Stop(self.status, 20),
            #LineTrace(self.status, power, 0.03, 0.8, trace_side = "left", func = self.in_blue, target = 0.3),
            Stop(self.status, 20),
            """Decisive(self.status, -60, -60, side = "left", count = -400), #元々-400
            Stop(self.status, 20),
            SelfPosition(self.status, very_slow, finish_position_x = 200, finish_position_y = -200, finish_position_a = -80),
            Stop(self.status, 20),
            SelfPosition(self.status, slow_power, finish_position_x = 300, finish_position_y = 0, finish_position_a = -110),
            Stop(self.status, 20),
            Decisive(self.status, 45, 65, func = self.in_black, type = "min"),
            Stop(self.status, 20),
            Decisive(self.status, 55, 0, func = self.in_black, type = "min"),
            Stop(self.status, 20),
            LineTrace(self.status, slow_power, 0.2, 0.8, trace_side = "right", side = "left", count = 1000),
        """
        ]
    
    def executer(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if self.state < len(self.state_list):
            if self.state_list[self.state].check_finish(right_motor, left_motor, color_sensor):
                self.status.reset(right_motor, left_motor)
                print(self.state + 1)
                self.state += 1
        
        if self.state < len(self.state_list):
            self.state_list[self.state].execute(right_motor, left_motor, color_sensor)
        else:
            right_motor.set_power(0)
            left_motor.set_power(0)



    def check_finish(self) -> bool:
        return self.state >= len(self.state_list)