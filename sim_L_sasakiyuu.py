# simulator　L_course
import argparse
#import time
from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor
from typing import Tuple


blue_pass = 0        

class LineTracer(object):
    def __init__(self, target: int, power: int, pid_p: float, pid_d: float, state:int, flag:bool) -> None:
        #self.running = False
        self.target = target
        self.power = power
        self.pid_p = pid_p
        self.pid_d = pid_d
        self.state = 1
        self.flag = False
        self.pid = PID(pid_p, pid_d)
        self.calibration = Calibration()
        self.scene = 1
        self.hsv = HSV()
        self.count = 0
        self.black_blue = False
        self.max_black = False
        


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
            self.calibration(right_motor, left_motor, color_sensor, self.add_scene)
        

        elif self.scene == 2:
            self.min_target, self.max_target, self.target = self.calibration.get_any_value()
            self.count = 0
            self.add_scene(2)


        elif self.scene == 3:
            power_ratio = self.pid(color_sensor, self.target, self.min_target, self.max_target)
            #黒の上ではマイナス

            
            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))

            right_motor.set_power(right_power)
            left_motor.set_power(left_power)
        
            print(self.hsv(color_sensor))
            s = self.hsv(color_sensor)
            
            if self.count > 100:
                if s > 0.55:
                    self.black_blue = True
            
            if self.black_blue:
                if s < 0.4:
                    self.black_blue = False
                    self.count = 0
                    self.add_scene(3)
            self.count += 1

        elif self.scene == 4:
            right_motor.set_power(-10)
            left_motor.set_power(-10)
            if self.count > 100:
                self.add_scene(4)
            self.count += 1
        
        elif self.scene == 5:
            color = color_sensor.get_raw_color()
            r = color[0]
            right_motor.set_power(30)
            left_motor.set_power(40)
            if r < self.min_target:
                self.max_black = True
            
            if self.max_black:
                if r > self.target:
                    self.add_scene(5)

        elif self.scene == 6:
            power_ratio = -self.pid(color_sensor, self.target, self.min_target, self.max_target)
            #白の上ではマイナス

            
            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))
        
            s = self.hsv(color_sensor)
            if self.count > 100:
                if s > 0.55:
                    self.black_blue = True
            
            if self.black_blue:
                if s < 0.4:
                    self.black_blue = False
                    self.count = 0
                    self.add_scene(6)
            self.count += 1
        
        elif self.scene == 7:
            power_ratio = -self.pid(color_sensor, self.target, self.min_target, self.max_target)
            #白の上ではマイナス

            
            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))


            right_motor.set_power(right_power)
            left_motor.set_power(left_power)
        
        print("r",color_sensor.get_raw_color()[0])
        print(self.scene)
        print(self.target)

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

    def __call__(self, color_sensor: ColorSensor, target, min_target, max_target) -> float:
        color = color_sensor.get_raw_color()
        r = color[0]

        e_r = 50 / (max_target - min_target) * (r - target)
        power_ratio = (self.pid_p * e_r) + ((e_r - self.e_r_previous) * self.pid_d)

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
        self.min_target = 50
        self.max_target = 50
        self.state = 1
        self.frame_count = 0
        self.flag = False
    
    def __call__(self, right_motor: Motor, left_motor: Motor, color_sensor: ColorSensor, add_scene) -> int:
        r = color_sensor.get_raw_color()[0]
        if self.state == 1:
            right_motor.set_power(20)
            left_motor.set_power(-20)
            if right_motor.get_count() > 50:
                self.frame_count = 0
                self.state = 2

        elif self.state == 2:
            right_motor.set_power(0)
            left_motor.set_power(0)
            if self.frame_count > 30:
                self.state = 3
        
        elif self.state == 3:
            right_motor.set_power(-20)
            left_motor.set_power(20)
            if right_motor.get_count() < -50:
                self.frame_count = 0
                self.state = 4
        
        elif self.state == 4:
            right_motor.set_power(0)
            left_motor.set_power(0)
            if self.frame_count > 30:
                self.state = 5
        
        elif self.state == 5:
            right_motor.set_power(20)
            left_motor.set_power(-20)
            if r <= self.min_target + 2:
                self.flag = True
            if right_motor.get_count() > 0 and self.flag:
                self.frame_count = 0
                self.state = 6
        
        elif self.state == 6:
            right_motor.set_power(0)
            left_motor.set_power(0)
            if self.frame_count > 30:
                add_scene(1)

        
        



        if self.min_target > r:
            self.min_target = r
        if self.max_target < r:
            self.max_target = r
        
        self.target = (self.min_target + self.max_target) // 2
        self.frame_count += 1
    
    def get_any_value(self):
        return self.min_target, self.max_target, self.target





def run(backend: str, target: int, power: int, pid_p: float, pid_d: float, state:int, flag:bool, **kwargs) -> None:
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
    parser.add_argument('--logfile', type=str, default=None, help='Path to log file')
    args = parser.parse_args()
    run(backend='simulator', target=46, power=90, pid_p=0.1, pid_d=0.5, state = 1, interval = 0.015, flag = False, logfile=args.logfile)