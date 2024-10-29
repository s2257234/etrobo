#ssh 192.168.0.2 -l etrobo# simulator　L_course
import argparse
# import time
from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor

blue_pass = 0

#木曜の練習用のためcountのifの設定が違う

class LineTracer(object):
    def __init__(self, target: int, power: int, pid_p: float,
                 pid_d: float, state: int, flag: bool) -> None:
        # self.running = False
        self.target = target
        self.power = power
        self.pid_p = pid_p
        self.pid_d = pid_d
        self.flag = False
        self.pid = PID(pid_p, pid_d)
        self.calibration = Calibration()
        self.scene = state
        self.hsv = HSV()
        self.count = 0
        self.black_blue = False
        self.max_black = False
        self.min_target = 20
        self.max_target = 200
        self.blue_flag = False
        self.blue_flag1 = False
        self.last_loop = False
        self.running = False


    def add_scene(self, scene):
        self.scene = scene + 1

    def __call__(
        self,
        hub: Hub,
        right_motor: Motor,
        left_motor: Motor,
        touch_sensor: TouchSensor,
        color_sensor: ColorSensor,
    ) -> None:
        if not self.flag:
            right_motor.reset_count()
            left_motor.reset_count()
            self.flag = True

        if self.scene == 1:
            self.calibration(right_motor, left_motor,
                             color_sensor, self.add_scene)

        elif self.scene == 2:
            self.min_target, self.max_target, self.target = self.calibration.get_any_value()
            # print(self.min_target, self.max_target, self.target)
            # 値の取得するクラス
            if not self.running and (
                    touch_sensor.is_pressed()
                    or hub.is_left_button_pressed()
                    or hub.is_right_button_pressed()):
                self.running = True
                self.count = 0

            if self.running:
                self.count += 1
                if self.count > 60:
                    self.add_scene(2)

        elif self.scene == 3:
            power_ratio = self.pid(
                color_sensor, self.target, self.min_target, self.max_target)
            # 黒の上ではマイナス

            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))

            right_power = int(right_power * 1.1)
            left_power = int(left_power * 1.1)

            #print(self.count)

            if (right_motor.get_count() > 3300 and right_motor.get_count() < 4700) or right_motor.get_count() > 5500:
                right_power = int(right_power * 0.7)
                left_power = int(left_power * 0.7)
                
            # print(self.hsv(color_sensor))
            s = self.hsv(color_sensor)

            # print(s)
            if self.count > 350: #本番では800より大きく
                right_power = int(right_power * 1.0)
                left_power = int(left_power * 1.0)
                if s > 0.29:  # 青色検知
                    self.black_blue = True  # 黒から青に乗ったことを検知

            if self.black_blue:
                if s < 0.27:
                    self.black_blue = False  # 黒から青に乗った後に黒に戻った
                    self.count = 0
                    self.add_scene(3)
            self.count += 1

            right_motor.set_power(right_power)
            left_motor.set_power(left_power)
            
        #lap後にスピードを落として青検地して黒検知して停止から方向を右側に向ける

        elif self.scene == 4: #円に乗るために方向転換
            #print(self.count)
            right_motor.set_brake(True) #ブレーキをかけた
            left_motor.set_brake(True)
            right_motor.set_power(0)
            left_motor.set_power(0)
            if self.count > 90:
                right_motor.set_brake(False) #ブレーキを解除
                left_motor.set_brake(False)
                right_motor.set_power(10)
                left_motor.set_power(30)
            if self.count > 100:
                self.count = 0
                self.add_scene(4)
            self.count += 1

        elif self.scene == 5: #円に乗るためのコード
            self.count += 1
            #print(self.count)
            color = color_sensor.get_raw_color()
            r = color[0]
            right_motor.set_power(38)
            left_motor.set_power(50)
            if r < self.min_target + 10:
                self.max_black = True

            if self.max_black:
                if r > self.target:
                    self.add_scene(5)
                    self.count = 0
                    self.max_black = False

        elif self.scene == 6: #円上をライントレース
            power_ratio = -self.pid(color_sensor, self.target,
                                    self.min_target, self.max_target)
            # 白の上ではマイナス

            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))

            right_power = int(right_power * 0.7)
            left_power = int(left_power * 0.7)

            right_motor.set_power(right_power)
            left_motor.set_power(left_power)

            s = self.hsv(color_sensor)
            #print("S:", s, "MotorCount", right_motor.get_count())

            if self.count > 50:
                if s > 0.25:  # 青色検知
                    self.black_blue = True  # 黒から青に乗ったことを検知

            if self.black_blue:
                if s < 0.15:
                    self.black_blue = False  # 黒から青に乗った後に黒に戻った
                    self.count = 0
                    self.add_scene(6)
            self.count += 1

        elif self.scene == 7: #青色を検知して停止
            right_motor.set_power(-0)
            left_motor.set_power(-0)
            if self.count > 75:
                self.add_scene(7)
            self.count += 1

        elif self.scene == 8: #楕円に入るために方向転換
            color = color_sensor.get_raw_color()
            r = color[0]
            right_motor.set_power(65)
            left_motor.set_power(0)
            if r < self.min_target + 10:
                self.max_black = True

            if self.max_black:
                if r > self.target:
                    self.add_scene(8)
                    self.count = 0
                    self.max_black = False

        elif self.scene == 9: #楕円上をライントレース
            power_ratio = self.pid.inloop(color_sensor, self.target,
                                          self.min_target, self.max_target)
            # 白の上ではマイナス

            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))

            right_power = int(right_power * 0.8) #０．７だった
            left_power = int(left_power * 0.57) #０．５だった

            right_motor.set_power(right_power)
            left_motor.set_power(left_power)

            s = self.hsv(color_sensor)

            # print(s)
            #print(self.count)
            #print(self.black_blue)

            if self.count > 80:
                if s > 0.28:  # 青色検知
                    self.black_blue = True  # 黒から青に乗ったことを検知

            if self.black_blue:
                if s < 0.20:
                    self.black_blue = False  # 黒から青に乗った後に黒に戻った
                    self.count = 0
                    self.add_scene(9)
            self.count += 1

        elif self.scene == 10: #円にもどるために停止
            right_motor.set_power(-0)
            left_motor.set_power(-0)
            if self.count > 75:
                self.add_scene(10)
            self.count += 1

        elif self.scene == 11: #円に乗る
            color = color_sensor.get_raw_color()
            r = color[0]
            right_motor.set_power(30)
            left_motor.set_power(40)
            if r < self.min_target + 10:
                self.max_black = True

            if self.max_black:
                if r > self.target:
                    self.add_scene(11)
                    self.max_black = False
                    self.count = 0
        
        elif self.scene == 12: #円をライントレース
            power_ratio = -self.pid(color_sensor, self.target,
                                         self.min_target, self.max_target)
            # 白の上ではマイナス

            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))

            right_power = int(right_power * 0.65)
            left_power = int(left_power * 0.65)

            right_motor.set_power(right_power)
            left_motor.set_power(left_power)

            s = self.hsv(color_sensor)

            #print(s)

            if self.count > 50:
                left_motor.reset_count()
                if s > 0.25:  # 青色検知
                    self.count = 0
                    self.last_loop = True
            
            if self.last_loop:
                #print(left_motor.get_count())
                if left_motor.get_count() > 80:
                    self.add_scene(12)

            self.count += 1

        elif self.scene == 13: #戻るための停止
            right_motor.set_power(-0)
            left_motor.set_power(-0)
            if self.count > 75:
                self.add_scene(13)
            self.count += 1

        elif self.scene == 14: #戻るための回転
            
            color = color_sensor.get_raw_color()
            r = color[0]
            right_motor.set_power(65)
            left_motor.set_power(0)

            s = self.hsv(color_sensor)
            b = color[2]

            if s < 0.2:
                self.blue_flag = True
                self.count = 0

            if self.blue_flag:
                if s > 0.30: #試走会で0.35だった
                    self.blue_flag1 = True
                    self.count = 0

            if self.blue_flag1:
                if b < 90:
                    self.count = 0
                    self.add_scene(14)

        elif self.scene == 15:
            right_motor.set_power(-0)
            left_motor.set_power(-0)
            if self.count > 75:
                self.add_scene(15)
                self.count = 0
            self.count += 1

        elif self.scene == 16:
            power_ratio = -self.pid(color_sensor, self.target,
                                         self.min_target, self.max_target)
            # 白の上ではマイナス

            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))
            right_power = int(right_power * 0.6)
            left_power = int(left_power * 0.6)

            right_motor.set_power(right_power)
            left_motor.set_power(left_power)

            self.count += 1

            if self.count > 300:
                right_power = int(right_power * 1.3)
                left_power = int(left_power * 1.3)

                right_motor.set_power(right_power)
                left_motor.set_power(left_power)
    
        




class PID:
    def __init__(
        self,
        pid_p,
        pid_d
    ) -> None:
        self.pid_p = pid_p
        self.pid_d = pid_d
        self.e_r_previous = 0
        self.calibration = Calibration()

    def __call__(self, color_sensor: ColorSensor, target, min_target,
                 max_target) -> float:
        color = color_sensor.get_raw_color()
        r = color[0]

        e_r = 50 / (max_target - min_target) * (r - target)
        power_ratio = (self.pid_p * e_r) + \
            ((e_r - self.e_r_previous) * self.pid_d)

        self.e_r_previous = e_r
        return power_ratio

    def inloop(self, color_sensor: ColorSensor, target,
               min_target, max_target) -> float:
        color = color_sensor.get_raw_color()
        r = color[0]

        self.pid_p = 0.1
        self.pid_d = 1.2

        e_r = 50 / (max_target - min_target) * (r - target)
        power_ratio = (self.pid_p * e_r) + \
            ((e_r - self.e_r_previous) * self.pid_d)

        self.e_r_previous = e_r
        return power_ratio


class HSV:
    def __init__(self) -> None:
        pass

    def __call__(self, color_sensor: ColorSensor) -> float:
        self.color = color_sensor.get_raw_color()
        max_value = max(self.color)
        min_value = min(self.color)
        s = (max_value - min_value) / max_value
        return s


# できるかどうかわかりません
# キャリブレーションを行うクラス
class Calibration:
    def __init__(self) -> None:
        self.min_target = 255
        self.max_target = 0
        self.state = 0
        self.frame_count = 0
        self.flag = False
        self.motor_count = 0

    def __call__(self, right_motor: Motor, left_motor: Motor,
                 color_sensor: ColorSensor, add_scene):
        r = color_sensor.get_raw_color()[0]
        print(self.flag, self.min_target, self.max_target)
        if self.state == 0:
            b = color_sensor.get_raw_color()
            right_motor.set_power(0)
            left_motor.set_power(0)
            if self.frame_count > 100:
            #if right_motor.get_count() == 0:
                self.state = 1

        if self.state == 1:
            right_motor.set_power(65)
            left_motor.set_power(0)
            if right_motor.get_count() > 50:
                self.frame_count = 0
                self.state = 2

        elif self.state == 2:
            right_motor.set_power(0)
            left_motor.set_power(0)
            self.motor_count = right_motor.get_count()
            if self.frame_count > 30:
                self.state = 3

        elif self.state == 3:
            right_motor.set_power(-65)
            left_motor.set_power(0)
            if right_motor.get_count() < -50:
                self.frame_count = 0
                self.state = 4

        elif self.state == 4:
            right_motor.set_power(0)
            left_motor.set_power(0)
            if self.frame_count > 30:
                self.state = 5

        elif self.state == 5:
            right_motor.set_power(65)
            left_motor.set_power(0)
            if r <= self.min_target + 10:
                self.flag = True
            if right_motor.get_count() > 0 and self.flag:
                self.frame_count = 0
                self.state = 6

        elif self.state == 6:
            right_motor.set_power(0)
            left_motor.set_power(0)
            if self.frame_count > 30:
                add_scene(1)

        if self.state > 0:
            if self.min_target > r:
                self.min_target = r
            if self.max_target < r:
                self.max_target = r

        self.target = (self.min_target + self.max_target) // 2
        self.frame_count += 1

    def get_any_value(self):
        return self.min_target, self.max_target, self.target


def run(backend: str, target: int, power: int, pid_p: float, pid_d: float,
        state: int, flag: bool, **kwargs) -> None:
    (ETRobo(backend=backend)
     .add_hub('hub')
     .add_device('right_motor', device_type=Motor, port='B')
     .add_device('left_motor', device_type=Motor, port='C')
     .add_device('touch_sensor', device_type=TouchSensor, port='1')
     .add_device('color_sensor', device_type=ColorSensor, port='2')
     .add_handler(LineTracer(target, power, pid_p, pid_d, state, flag))
     .dispatch(**kwargs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', type=str,
                        default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='raspyke', target=110, power=80, pid_p=0.063, pid_d=0.625,
        state=1, interval=0.015, flag=False, logfile=args.logfile)
