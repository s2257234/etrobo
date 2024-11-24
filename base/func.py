from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor

from status import Status
import math
from typing import Tuple

#PID計算を行うクラス
class PID(object):
    def __init__(self, p: float, d: float, status: Status) -> None:
        self.p = p
        self.d = d
        self.status = status

# 計算を行うメソッド
    def math(self) -> int:
        # print(self.p * self.status.e_red , (self.status.e_red - self.status.prev_e_red) * self.d)
        power_ratio = (self.p * self.status.e_red) + ((self.status.e_red - self.status.prev_e_red) * self.d)
        return power_ratio
    
    def math_s(self) -> int:
        power_ratio = -((self.p * self.status.e_s) + ((self.status.e_s - self.status.prev_e_s) * self.d))
        return power_ratio







# 青線に入ったことを検知するクラス
class InBlue(object):
    def give_target(self, target) -> None:
        self.target = target

    def judgement(self, status: Status) -> None:  
        self.s = status.s
        return self.s > self.target


# 青線から出たことを検知するクラス
class OutBlue(object):
    def give_target(self, target) -> None:
        self.target = target

    def judgement(self, status: Status) -> None:  
        self.s = status.s
        return self.s < self.target



# 黒線の中心を超えたことを検知するクラス（黒線をまたぐときに利用する）
class MinBlackPass(object):
    def give_target(self, target: int) -> None:
        pass

    def judgement(self, status: Status) -> None:  
        self.red = status.red
        return self.red < status.min_target_red + 5



# 白色から黒線に入ったことを検知するクラス
class InMiddleBlack(object):
    def give_target(self, target: int) -> None:
        pass

    def judgement(self, status: Status) -> None:
        self.red = status.red
        return self.red < status.target_red



# 黒線から白色に入ったことを検知するクラス
class OutMiddleBlack(object):
    def give_target(self, target: int) -> None:
        pass

    def judgement(self, status: Status) -> None: 
        self.red = status.red
        return self.red > status.target_red











# 停止処理を行うクラス
# 終了条件は何フレーム経ったか（1フレーム = 1インターバル）
class Stop(object):
    def __init__(self, status: Status, finish_count: int) -> None:
        self.status = status
        self.frame_count = 0
        self.finish_count = finish_count


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
    def __init__(self, status: Status ,right_power: int, left_power: int, **finish) -> None:
        self.status = status
        self.right_power = right_power
        self.left_power = left_power
        self.side = "nothing"
        self.finish_type = "none"

        for key, value in finish.items():
            # 回転数の場合
            if key == "side":
                self.side = value
            if key == "count":
                self.finish_count = value
            
            # 特定のものの検知の場合
            if key == "target":
                self.finish_target = value
            if key == "type":
                self.finish_type = str(value)
                if self.finish_type == "max":
                    self.finish_target = self.status.max_target_red
                elif self.finish_type == "min":
                    self.finish_target = self.status.min_target_red + 5
                else:
                    self.finish_target = self.status.target_red
            if key == "func":
                self.finish_func = value
        
        # 一回実行のためのフラグ
        self.first_time_flag = True
    


# 終了条件を検知するメソッド
# Trueなら終了、Falseなら続行
# 終了条件が関数の場合はside = "nothing"になるため、終了条件の結果をリターンする
# タイヤの場合はどちらの側のタイヤを利用するかと、目標回転数の正負によって分岐させている
    def check_finish(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> bool:
        if self.side == "nothing":
            self.finish_func.give_target(self.finish_target)
            return self.finish_func.judgement(self.status)
        else:
            if self.side == "right":
                if self.finish_count > 0:
                    return self.finish_count < self.status.right_count
                else:
                    return self.finish_count > self.status.right_count
            elif self.side == "left":
                if self.finish_count > 0:
                    return self.finish_count < self.status.left_count
                else:
                    return self.finish_count > self.status.left_count
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
    def __init__(self, status: Status,power: int, pid_p: float, pid_d: float, **finish) -> None:
        self.status = status
        self.power = power
        self.pid = PID(pid_p, pid_d, self.status)
        self.side = "nothing"
        self.s_trace = False

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
            if key == "special":
                self.s_trace = True


# 終了条件を確認するメソッド
    def check_finish(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> bool:
        if self.side == "nothing":
            self.finish_func.give_target(self.finish_target)
            return self.finish_func.judgement(self.status)
        else:
            if self.side == "right":
                if self.finish_count > 0:
                    return self.finish_count < self.status.right_count
                else:
                    return self.finish_count > self.status.right_count
            elif self.side == "left":
                if self.finish_count > 0:
                    return self.finish_count < self.status.left_count
                else:
                    return self.finish_count > self.status.left_count

# 実行するメソッド
# PID計算の結果をもとに値を求め送る
    def execute(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if self.s_trace:
            if self.trace_side == "right":
                power_ratio = -self.pid.math_s()
            else:
                power_ratio = self.pid.math_s()

            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = int(self.power)
            else:
                right_power = int(self.power)
                left_power = int(self.power / (1 - power_ratio))

            right_motor.set_power(right_power)
            left_motor.set_power(left_power)

        else:
            if self.trace_side == "right":
                power_ratio = -self.pid.math()
            else:
                power_ratio = self.pid.math()

            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = int(self.power)
            else:
                right_power = int(self.power)
                left_power = int(self.power / (1 - power_ratio))
            
            
            # print(left_power, right_power)

            right_motor.set_power(right_power)
            left_motor.set_power(left_power)



# 自己位置推定を行った走行を行うクラス
class SelfPosition(object):
    def __init__(self, status: Status, base_motor_power: int, **finish) -> None:
        self.status = status
        self.base_motor_power = base_motor_power
        self.finish_func = "none"
        self.finish_position_a = 0
        self.self_position_estimation = SelfPositionEstimation(self.status)
        self.finish_flag = False

        for key, value in finish.items():
            if key == "target":
                self.finish_target = value
            if key == "type":
                self.finish_type = str(value)
                if self.finish_type == "max":
                    self.finish_target = self.status.max_target_red
                elif self.finish_type == "min":
                    self.finish_target = self.status.min_target_red + 5
                else:
                    self.finish_target = self.status.target_red
            if key == "func":
                self.finish_func = value

            
            if key == "finish_position_x":
                self.finish_position_x = value
            if key == "finish_position_y":
                self.finish_position_y = value
            if key == "finish_position_a":
                self.finish_position_a = math.radians(value)
    
    def check_finish(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> bool:
        if self.finish_func == "none":
            if self.finish_position_a == 0:
                return self.self_position_estimation.check_finish_xy(right_motor, left_motor, color_sensor)
            else:
                if self.self_position_estimation.check_finish_xy(right_motor, left_motor, color_sensor):
                    self.finish_flag = True
                if self.finish_flag:
                    return self.self_position_estimation.check_finish_a(right_motor, left_motor, color_sensor)

        else:
            self.finish_func.give_target(self.finish_target)
            return self.finish_func.judgement(self.status)
    
    def execute(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> None:
        if self.finish_flag == False:
            left_power, right_power = self.self_position_estimation.math_xy(self.finish_position_x, self.finish_position_y)
        else:
            left_power, right_power = self.self_position_estimation.math_a(self.finish_position_a)
        
        left_power_last = int(left_power * self.base_motor_power)
        right_power_last = int(right_power * self.base_motor_power)

        # 実際環境に近づけるために最低値を設定
        if abs(left_power_last) < 30:
            left_power_last = 0
        if abs(right_power_last) < 30:
            right_power_last = 0

        
        right_motor.set_power(right_power_last)
        left_motor.set_power(left_power_last)



# 自己位置推定を行うクラス
# 現在自己位置推定の計算は終わっており、statusには位置情報が入っている
# 行うべきことは、ゴール地点との差分を計算し、モーターの回転比率を特定することである
class SelfPositionEstimation(object):
    def __init__(self, status: Status) -> None:
        self.status = status
        self.abs_x = 1000
        self.abs_y = 1000
        self.abs_a = 1000
    
    def math_xy(self, finish_position_x: int, finish_position_y: int) -> Tuple[int, int]:

        abs_x = finish_position_x - self.status.position_x
        abs_y = finish_position_y - self.status.position_y

        self.abs_x = abs_x
        self.abs_y = abs_y

        cos_a = math.cos(self.status.position_a)
        sin_a = math.sin(self.status.position_a)
        rel_x = abs_x * cos_a + abs_y * sin_a
        rel_y = -abs_x * sin_a + abs_y * cos_a
        direction = math.atan2(rel_y, rel_x)

        if direction > 0.0:
            return 1.0, 1.0 / (1 + direction * 1)
        else:
            return 1.0 / (1 - direction * 1), 1.0
    

    def math_a(self, finish_position_a: int) -> int:
        abs_a = finish_position_a - self.status.position_a
        self.abs_a = abs_a
        
        # この場合はずれる可能性大
        # 1と0にするのが最適だが、終了座標がその分ずれるため注意
        if abs_a > 0.0:
            return 0.9, -0
        else:
            return -0, 0.9
    
    def check_finish_xy(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> bool:
        if self.abs_x <= 0 and self.abs_y <= 0:
            return True
        return False
    
    def check_finish_a(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor) -> bool:
        if abs(self.abs_a) <= 0.05:
            return True
        return False
