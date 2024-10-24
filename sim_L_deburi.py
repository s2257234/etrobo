import argparse
from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor



#PID計算を行うクラス
class PID(object):
    def __init__(self, p: float, d: float) -> None:
        self.p = p
        self.d = d
        self.prev_e_red = 0

# 計算に必要な各種変数を受け取る（キャリブレーションを基に受け取るためインスタンス生成時には間に合わないから）
    def give_any_value(self, target: int, min_target: int, max_target: int) -> None:
        self.target = target
        self.min_target = min_target
        self.max_target = max_target

# 計算を行うメソッド
    def math(self, color_sensor: ColorSensor) -> int:
        red = color_sensor.get_raw_color()[0]

        e_red = 50 / (self.max_target - self.min_target) * (red - self.target)
        power_ratio = (self.p * e_red) + ((e_red - self.prev_e_red) * self.d)

        self.prev_e_red = e_red
        return power_ratio





# HSVのSを計算するクラス
class HSV_S(object):
    def __call__(self, color_sensor: ColorSensor) -> None:
        self.color = color_sensor.get_raw_color()
        max_value = max(self.color)
        min_value = min(self.color)
        s = (max_value - min_value) / max_value
        return s



# 青線に入ったことを検知するクラス
class InBlue(object):
    def give_target(self, target) -> None:
        self.target = target
        self.hsv_s = HSV_S()

    def judgement(self, color_sensor: ColorSensor) -> None:  
        self.s = self.hsv_s(color_sensor)
        return self.s > self.target


# 青線から出たことを検知するクラス
class OutBlue(object):
    def give_target(self, target) -> None:
        self.target = target
        self.hsv_s = HSV_S()

    def judgement(self, color_sensor: ColorSensor) -> None:  
        self.s = self.hsv_s(color_sensor)
        return self.s < self.target



# 黒線の中心を超えたことを検知するクラス（黒線をまたぐときに利用する）
class MinBlackPass(object):
    def give_target(self, target: int) -> None:
        self.target = target

    def judgement(self, color_sensor: ColorSensor) -> None:
        self.red = color_sensor.get_raw_color()[0]
        return self.red < self.target



# 白色から黒線に入ったことを検知するクラス
class InMiddleBlack(object):
    def give_target(self, target: int) -> None:
        self.target = target

    def judgement(self, color_sensor: ColorSensor) -> None:
        self.red = color_sensor.get_raw_color()[0]
        return self.red < self.target



# 黒線から白色に入ったことを検知するクラス
class OutMiddleBlack(object):
    def give_target(self, target: int) -> None:
        self.target = target

    def judgement(self, color_sensor: ColorSensor) -> None:
        self.red = color_sensor.get_raw_color()[0]
        return self.red > self.target



# 停止処理を行うクラス
# 終了条件は何フレーム経ったか（1フレーム = 1インターバル）
class Stop(object):
    def __init__(self, finish_count: int) -> None:
        self.frame_count = 0
        self.finish_count = finish_count


    # 不要だが、ライントレース、決め打ち両方のクラスにgiveメソッドが存在するため記述しました。
    def give_target(self, target: int, min_target: int, max_target:int) -> None:
        pass


# 終了を検知するメソッド（Trueなら終了、Falseなら実行）
    def check_finish(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> bool:
        self.frame_count += 1
        if self.frame_count >= self.finish_count:
            return True
        return False


# 実際に実行するクラス
    def execute(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        right_motor.set_power(0)
        right_motor.set_brake(True)
        left_motor.set_power(0)
        left_motor.set_brake(True)



# 決め打ち制御を行うクラス
# 終了条件が特定のものの検知と、回転数が一定数値になったらの二パターンがあるため、引数は限定していません。

# 特定のものの検知の場合は、終了条件になるものの検知を行うクラスをインスタンス化して送り、目標数値も送る
# その時は右の様に記述する　　　func = インスタンス生成終わった関数, target = 終了条件に必要な数値

# 回転数が一定になる場合はどちらのタイヤを基にするかのsideと指定回転数のcountを送る
#                            side = "right" or "left" , count = 終了徒らる回転数の数値
class Decisive(object):
    def __init__(self, right_power: int, left_power: int, **finish) -> None:
        self.right_power = right_power
        self.left_power = left_power
        self.side = "nothing"

        for key, value in finish.items():
            if key == "side":
                self.side = value
            if key == "count":
                self.finish_count = value
            if key == "target":
                self.finish_target = value
            if key == "type":
                self.finish_type = str(value)
            if key == "func":
                self.finish_func = value


# ライントレースクラスにgiveメソッドがあり、また、キャリブレーションで用いた値を投げる必要があるため作ったgiveメソッドです。
    def give_target(self, target: int, min_target: int, max_target: int) -> None:
        self.target = target
        self.min_target = min_target
        self.max_target = max_target

        if self.finish_type == "min":
            self.finish_target = min_target + 5
        elif self.finish_type == "max":
            self.finish_target = max_target
        else:
            self.finish_target = target


# 終了条件を検知するメソッド
# Trueなら終了、Falseなら続行
# 終了条件が関数の場合はside = "nothing"になるため、終了条件の結果をリターンする
# タイヤの場合はどちらの側のタイヤを利用するかと、目標回転数の正負によって分岐させている
    def check_finish(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> bool:
        if self.side == "nothing":
            self.finish_func.give_target(self.finish_target)
            return self.finish_func.judgement(color_sensor)
        else:
            if self.side == "right":
                if self.finish_count > 0:
                    return self.finish_count < right_motor.get_count()
                else:
                    return self.finish_count > right_motor.get_count()
            elif self.side == "left":
                if self.finish_count > 0:
                    return self.finish_count < left_motor.get_count()
                else:
                    return self.finish_count > left_motor.get_count()
        return True


# 決まられた回転で実行する
    def execute(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        right_motor.set_power(self.right_power)
        left_motor.set_power(self.left_power)



# ライントレースを行うクラス
# 上と同様に終了条件に複数パターンがあるため同様の書き方をしている。
# キャリブレーション中には利用されないため、特殊な値を受け取るメソッドはない。
# しかし、キャリブレーションの結果を利用するため値を受け取るメソッドは存在する。
# またPIDを利用するため、PIDクラスに渡す値も必要である。
class LineTrace(object):
    # finishは回転数を指定する場合はint型とどちらの回転数を利用するか(side)(str型)、関数を指定する場合は関数を指定する
    def __init__(self, power: int, pid_p: float, pid_d: float, **finish) -> None:
        self.power = power
        self.pid = PID(pid_p, pid_d)
        self.side = "nothing"

        for key, value in finish.items():
            if key == "side":
                self.side = value
            if key == "count":
                self.finish_count = value
            if key == "target":
                self.finish_target = value
            if key == "trace_side":
                self.trace_side = value
            if key == "func":
                self.finish_func = value

# 各種値を設定し、PIDにも値を投げるメソッド
    def give_target(self, target: int, min_target: int, max_target: int) -> int:
        self.target = target
        self.min_target = min_target
        self.max_target = max_target
        self.pid.give_any_value(target, min_target, max_target)

# 終了条件を確認するメソッド
    def check_finish(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> bool:
        if self.side == "nothing":
            self.finish_func.give_target(self.finish_target)
            return self.finish_func.judgement(color_sensor)
        else:
            if self.side == "right":
                if self.finish_count > 0:
                    return self.finish_count < right_motor.get_count()
                else:
                    return self.finish_count > right_motor.get_count()
            elif self.side == "left":
                if self.finish_count > 0:
                    return self.finish_count < left_motor.get_count()
                else:
                    return self.finish_count > left_motor.get_count()

# 実行するメソッド
# PID計算の結果をもとに値を求め送る
    def execute(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if self.trace_side == "right":
            power_ratio = -self.pid.math(color_sensor)
        else:
            power_ratio = self.pid.math(color_sensor)
        if power_ratio > 0:
            right_power = int(self.power / (1 + power_ratio))
            left_power = int(self.power)
        else:
            right_power = int(self.power)
            left_power = int(self.power / (1 - power_ratio))

        right_motor.set_power(right_power)
        left_motor.set_power(left_power)




# シーンです
# execute"r"です
# 最終的には1つにまとめてもよいが、現状はキャリブレーションシーン、ライントレースシーン、
# ダブルループシーン、デブリリムーバルシーン、スマートキャリーシーンに分割されると思われる

# ここで走行計画を立てて、各種変数を送るため、ここでの与える引数がパラメータとなる
class CalibrationScene(object):
    def __init__(self, state: int) -> None:
        self.state = state
        self.min_target = 255
        self.max_target = 0
        self.target = 0
        self.black_to_white = OutMiddleBlack()
        self.white_to_black = InMiddleBlack()
        self.in_black = MinBlackPass() 
        self.state_list = [
            Stop(10),
            Decisive(50, 0, side = "right", count = 100),
            Stop(50),
            Decisive(-60, 0, side = "right", count = -200),
            Stop(50),
            Decisive(60, 0, func = self.white_to_black, type = "midi"),
            Decisive(60, 0, func = self.in_black, type = "midi"),
            Stop(55),
        ]


    def executer(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        red = color_sensor.get_raw_color()[0]
        if red < self.min_target:
            self.min_target = red
        if red > self.max_target:
            self.max_target = red
        self.target = (self.min_target + self.max_target) // 2

        if self.state < len(self.state_list):
            # 4,5は前の決め打ちから求めた値を利用する必要があるため、ここで一度値を渡す処理を挟んでいる
            if self.state == 5:
                self.state_list[self.state].give_target(self.target, self.min_target, self.max_target)
                self.state_list[self.state + 1].give_target(self.target, self.min_target, self.max_target)
            if self.state_list[self.state].check_finish(right_motor, left_motor, color_sensor):
                right_motor.reset_count()
                left_motor.reset_count()
                self.state += 1
        
        if self.state < len(self.state_list):
            self.state_list[self.state].execute(right_motor, left_motor, color_sensor)
        else:
            pass


# キャリブレーションで求めた各種値を返すためのメソッド
    def get_any_value(self) -> int:
        return self.target, self.min_target, self.max_target

# キャリブレーションシーンが終わったことを確認するメソッド
# Trueなら終了、Falseなら続行
    def check_finish(self) -> bool:
        return self.state >= len(self.state_list)





# ライントレースを行うシーン
# 親クラスでキャリブレーションが終わったタイミングで各種値を与えるためgiveメソッドがあります。
class Pattern1_deburi(object):
    def __init__(self, power: int, state:int) -> None:
        # ダブルループのためのフラグ
        self.state = state
        fast = power * 1.4
        slow = power * 0.8
        very_slow = power * 0.6
        self.in_blue = InBlue()
        self.out_blue = OutBlue()
        self.out_black = OutMiddleBlack()
        self.in_black = InMiddleBlack()

        self.state_list = [
            LineTrace(slow, 0.025, 0.45, trace_side = "left",func = self.in_blue, target = 0.3),
            Stop(50), #最初の青色検知➀
            Decisive(-40, 60, func = self.in_black, type = "min"), #右に曲がる
            Stop(50),
            Decisive(-40, 60, func = self.out_black, type = "midi"),
            Stop(50), 
            LineTrace(slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50), #青色検知➁
            LineTrace(slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),
            LineTrace(slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),
            LineTrace(very_slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),#ボトル検知前はvery_slow,直進時はLinetraceを二段階挟んでいる
            Stop(50), #本来は緑検知
            #Decisive(60, 60, side = "right", count = 10), #アーム上げるために後退させる
            #ここでアームを上げる
            Decisive(-40, 60, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(-40, 60, func = self.out_black, type = "midi"),
            Stop(50), #反転完了
            LineTrace(slow, 0.025, 0.45, trace_side = "left", func = self.in_blue, target = 0.3),# 高速
            Stop(50),#青色検知➁に戻る
            LineTrace(slow, 0.025, 0.45, trace_side = "left", func = self.in_blue, target = 0.3),
            Stop(50),#青色検知➀に戻る
            Decisive(-40, 60, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(-40, 60, func = self.out_black, type = "midi"),
            Stop(50),
            LineTrace(slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),#➃青検知
            Decisive(-40, 60, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(-40, 60, func = self.out_black, type = "midi"),
            Stop(50),
            LineTrace(very_slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),#➄青検知
            #アーム上げるとか諸々の動作
            Decisive(-40, 60, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(-40, 60, func = self.out_black, type = "midi"),
            Stop(50),
            Decisive(-40, 60, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(-40, 60, func = self.out_black, type = "midi"),
            Stop(50), #反転完了
            LineTrace(slow, 0.025, 0.45, trace_side = "left", func = self.in_blue, target = 0.3),# 高速
            Stop(50),#➅の青検知
            Decisive(60, -40, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(60, -40, func = self.out_black, type = "midi"),
            Stop(50),
            LineTrace(slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),#➆の赤検知
            LineTrace(very_slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),#➇の赤検知
            #アーム下げるとか諸々の動作
            Decisive(60, -40, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(60, -40, func = self.out_black, type = "midi"),
            Stop(50),#反転完了
            LineTrace(slow, 0.025, 0.45, trace_side = "left", func = self.in_blue, target = 0.3),# 高速
            Stop(50),#➈の赤検知
            Decisive(60, -40, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(60, -40, func = self.out_black, type = "midi"),
            Stop(50),
            LineTrace(slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),#➉の赤検知
            LineTrace(very_slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),#11の黄色検知
            #アーム下げるとか諸々の動作
            Decisive(60, -40, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(60, -40, func = self.out_black, type = "midi"),
            Stop(50),
            Decisive(60, -40, func = self.in_black, type = "min"),
            Stop(50),#反転完了
            LineTrace(slow, 0.025, 0.45, trace_side = "left", func = self.in_blue, target = 0.3),# 高速
            Stop(50),#11の赤検知
            Decisive(-40, 60, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(-40, 60, func = self.out_black, type = "midi"),
            Stop(50),
            LineTrace(slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),#12の赤検知
            Decisive(-40, 60, func = self.in_black, type = "min"),
            Stop(50),
            Decisive(-40, 60, func = self.out_black, type = "midi"),
            Stop(50),
            LineTrace(very_slow, 0.025, 0.45, trace_side = "right", func = self.in_blue, target = 0.3),
            Stop(50),#スマートキャリーへ
        ]

        self.first_flag = False


    def give_any_value(self, target: int, min_target: int, max_target: int) -> None:
        for state in self.state_list:
            state.give_target(target, min_target, max_target)

    
    def check_finish(self) -> bool:
        return self.state >= len(self.state_list)


    def executer(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if not self.first_flag:
            right_motor.reset_count()
            left_motor.reset_count()
            self.first_flag = True
            

        if self.state < len(self.state_list):
            if self.state_list[self.state].check_finish(right_motor, left_motor, color_sensor):
                right_motor.reset_count()
                left_motor.reset_count()
                self.state += 1
        
        if self.state < len(self.state_list):
            self.state_list[self.state].execute(right_motor, left_motor, color_sensor)
        else:
            right_motor.set_power(0)
            left_motor.set_power(0)



# ダブルループシーンのクラス
# 上と同様にキャリブレーションで求めた値を利用するため、giveメソッドがあります。
class DoubleLoopScene(object):
    def __init__(self, power: int, state:int) -> None:
        self.state = state
        self.in_blue = InBlue()
        self.out_blue = OutBlue()
        self.over_black = MinBlackPass()
        self.out_black = OutMiddleBlack()
        self.in_black = InMiddleBlack()
        slow = power * 0.7
        very_slow = power * 0.25
        self.state_list = [
            # 1つ目のループに入るため
            Stop(70),
            Decisive(40, 60, func = self.over_black, type = "min"),
            Decisive(40, 45, func = self.out_black, type = "midi"),
            Stop(70),

            # 1つ目のループ
            LineTrace(slow, 0.2, 0.8, trace_side = "right", func = self.in_blue, target = 0.3),
            LineTrace(slow, 0.2, 0.8, trace_side = "right", func = self.out_blue, target = 0.15),

            # 2つ目のループに入るため
            Stop(70),
            Decisive(60, 50, func = self.in_black, type = "midi"),
            Stop(70),

            # 2つ目のループ
            LineTrace(slow, 0.2, 0.8, trace_side = "left", func = self.in_blue, target = 0.3),
            LineTrace(slow, 0.2, 0.8, trace_side = "left", func = self.out_blue, target = 0.15),

            # 1つ目のループに入るため
            Stop(70),
            Decisive(50, 60, func = self.over_black, type = "min"),
            Decisive(50, 60, func = self.out_black, type = "midi"),
            Stop(70),

            # 1つ目のループ
            LineTrace(slow, 0.2, 0.8, trace_side = "right", func = self.in_blue, target = 0.3),
            LineTrace(slow, 0.2, 0.8, trace_side = "right", func = self.out_blue, target = 0.15),

            # 抜けるため
            Stop(70),
            Decisive(40, 40, func = self.over_black, type = "min"),
            Decisive(40, 45, func = self.out_black, type = "midi"),
            Stop(70),
        ]


    def give_any_value(self, target: int, min_target: int, max_target: int) -> None:
        for state in self.state_list:
            state.give_target(target, min_target, max_target)


    def executer(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if self.state < len(self.state_list):
            if self.state_list[self.state].check_finish(right_motor, left_motor, color_sensor):
                right_motor.reset_count()
                left_motor.reset_count()
                self.state += 1
        
        if self.state < len(self.state_list):
            self.state_list[self.state].execute(right_motor, left_motor, color_sensor)
        else:
            right_motor.set_power(0)
            left_motor.set_power(0)


    def check_finish(self) -> bool:
        return self.state >= len(self.state_list)







class Runner(object):
    def __init__(self, power: int, state:int, flag:bool) -> None:
        self.power = power
        self.state = state
        self.running = flag
        self.first_time_flag = True
        self.calibration = CalibrationScene(0)
        self.scene_list = [
            Pattern1_deburi(power, 0),
            #DoubleLoopScene(power, 0),
            ]

    def __call__(self, hub: Hub, right_motor: Motor, left_motor: Motor, touch_sensor: TouchSensor, color_sensor: ColorSensor) -> None:
        if self.running and self.first_time_flag:
            target, min_target, max_target = 46, 10, 80
            for state in self.scene_list:
                state.give_any_value(target, min_target, max_target)
            self.first_time_flag = False
        else:
            self.calibration.executer(right_motor, left_motor, color_sensor)
            if self.calibration.check_finish() and (
                    touch_sensor.is_pressed()
                    or hub.is_left_button_pressed()
                    or hub.is_right_button_pressed()):
                target, min_target, max_target = self.calibration.get_any_value()
                for state in self.scene_list:
                    state.give_any_value(target, min_target, max_target)
                self.running = True
            
        if self.running:
            if self.scene_list[self.state].check_finish():
                right_motor.reset_count()
                left_motor.reset_count()
                self.state += 1
            else:
                self.scene_list[self.state].executer(right_motor, left_motor, color_sensor)





def run(backend: str, power: int, state:int, flag:bool, **kwargs) -> None:
    (ETRobo(backend=backend)
     .add_hub('hub')
     .add_device('right_motor', device_type=Motor, port='B')
     .add_device('left_motor', device_type=Motor, port='C')
     .add_device('touch_sensor', device_type=TouchSensor, port='1')
     .add_device('color_sensor', device_type=ColorSensor, port='2')
     .add_handler(Runner(power, state, flag))
     .dispatch(**kwargs))




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='simulator', power=90, state = 0, interval = 0.015, flag = False, logfile=args.logfile)
