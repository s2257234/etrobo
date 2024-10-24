import argparse
#import time
from etrobo_python import ColorSensor, ETRobo, Hub, Motor, TouchSensor

blue_pass = 0        

class LineTracer(object):
    def __init__(self, target: int, power: int, pid_p: float, pid_d: float, state:int, flag:bool) -> None:
        #self.running = False
        self.target = target
        self.power = power
        self.pid_p = pid_p
        self.pid_d = pid_d
        self.e_r_previous = 0
        self.state = 1
        self.flag = False

        
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
        
        """if not self.running:
            color = color_sensor.get_raw_color()
            return"""

        #colorの値を取り終わった後に
        #brightness = color_sensor.get_brightness() - self.target

        #brightnessの正しい値を表示
        #brightness = color_sensor.get_brightness()
        #print(brightness)


        #power_ratio = self.pid_p * brightness
        left_power = self.power
        # RGB
        color = color_sensor.get_raw_color()
        #print(color)
        motor_count = right_motor.get_count() + left_motor.get_count() // 2
        print(motor_count) 
        
        r = color[0]
        g = color[1]
        b = color[2]


        e_r = r - self.target
        power_ratio = (self.pid_p * e_r) + ((e_r - self.e_r_previous) * self.pid_d)
        #黒の上ではマイナス

        
        maxi, mid, mini = sorted(color, reverse=True)
        # print("----------------------------------------------------------")
        #print("色",color)
        # print("brightness:",brightness)
        # print(e_g)

        # if maxi != 0:
        #     if r > g and r > b:
        #         h = 60 * ((g - b) / (maxi - mini))
        #     elif g > r and g > b:
        #         h = 60 * ((r - b) / (maxi - mini)) + 120
        #     elif b > r and b > g:
        #         h = 60 * ((r - g) / (maxi - mini)) + 240
        #     else:
        #         h = 0
        # else:
        #     maxi, mini = 1, 1

        # if h < 0:
        #     h += 360

        s = 255 * ((maxi - mini) / maxi )

        v = maxi

        #print("HSV:",round(h),round(s),v)
        print(self.state, "HSV:",round(s),v)
        print(color_sensor.get_raw_color())
        #print(power_ratio)
        
        if self.state == 1:
            if power_ratio > 0:
                right_power = int(self.power / (1 + power_ratio))
                left_power = self.power
            else:
                right_power = self.power
                left_power = int(self.power / (1 - power_ratio))
            
            if motor_count > 10500:
                self.state = 2

        #最黒の線を超えるまで右側には行かない

        """elif self.state == 2:
            if power_ratio > 0:
                right_power = self.power
                left_power = int(self.power / (1 + power_ratio))
            else:
                right_power = int(self.power / (1 - power_ratio))
                left_power = self.power"""


            

        

        



        
            
        #print(color[0],power_ratio, right_power, left_power)
        right_motor.set_power(right_power)
        left_motor.set_power(left_power)
        

        """if self.state == 3:
            right_motor.set_brake(True)
            left_motor.set_brake(True)"""

        #right_motor.set_power(50)
        #left_motor.set_power(50)
        # print(self.e_g_previous)
        self.e_r_previous = e_r
        

        #print(left_motor.get_count())
        #print(right_power,left_power)
        

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
    run(backend='simulator', target=95, power=90, pid_p=0.1, pid_d=0.75, state = 1, interval = 0.015, flag = False, logfile=args.logfile)
    #powerの値を
    #白、黒、青などの全部の値をとる（環境測定）
    #targetの値は白と黒の中心
    #コードを変えるときはコピー取ってから動くコード、動かないコード戻れるように

    #dの値を10倍してlt14.pyよりも揺れない
    #pの値を小さくしたら揺れが減るが小さすぎるとカーブが曲がり切れない



"""if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default='/dev/ttyAMA1', help='Serial port.')
    args = parser.parse_args()
    run(backend='raspyke', interval=0.15, target=60, power=60, pid_p=0.05)"""

